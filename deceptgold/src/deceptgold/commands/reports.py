import json
import os
import logging
import random
import sys
import time
import itertools
from collections import Counter
from datetime import datetime
from pathlib import Path

from cyclopts import App

from deceptgold.helper.helper import get_temp_log_path, NAME_FILE_LOG
from deceptgold.helper.ai_model import ensure_model_installed, list_installed_models


logger = logging.getLogger(__name__)
_SAMPLE_LIMIT = 40


def _is_interactive() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _iter_jsonl_lines_stream(path: Path):
    with path.open("rb") as f:
        for bline in f:
            try:
                yield bline.decode("utf-8", errors="ignore"), len(bline)
            except Exception:
                continue

reports_app = App(name="reports", help="Reports commands")


def _load_llm(model_path: str):
    from llama_cpp import Llama

    n_ctx = 4096
    n_threads = 0

    kwargs = {
        "model_path": model_path,
        "n_ctx": n_ctx,
        "verbose": False,
    }
    if n_threads > 0:
        kwargs["n_threads"] = n_threads

    return Llama(**kwargs)


def _truncate_any(value, limit: int):
    if value is None:
        return None
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…"
    if isinstance(value, (int, float, bool)):
        return value
    try:
        encoded = json.dumps(value, ensure_ascii=False)
        if len(encoded) <= limit:
            return value
        return _truncate_any(encoded, limit)
    except Exception:
        return _truncate_any(str(value), limit)


def _build_prompt_payload(aggregates: dict, sample_limit: int):
    def _top(name: str, n: int):
        items = aggregates.get(name) or []
        if not isinstance(items, list):
            return []
        out = []
        for it in items[:n]:
            if not isinstance(it, dict):
                continue
            out.append({"value": _truncate_any(it.get("value"), 80), "count": it.get("count")})
        return out

    payload = {
        "total_events": aggregates.get("total_events"),
        "time_range": aggregates.get("time_range"),
        "top_logtypes": _top("top_logtypes", 10),
        "top_sources": _top("top_sources", 10),
        "top_dst_ports": _top("top_dst_ports", 10),
        "top_services": _top("top_services", 10),
        "top_usernames": _top("top_usernames", 10),
        "top_paths": _top("top_paths", 10),
        "top_useragents": _top("top_useragents", 8),
    }

    samples = aggregates.get("event_samples") or []
    if isinstance(samples, list):
        slim = []
        for s in samples[:sample_limit]:
            if not isinstance(s, dict):
                continue
            slim.append(
                {
                    "timestamp": _truncate_any(s.get("timestamp"), 64),
                    "logtype": _truncate_any(s.get("logtype"), 32),
                    "service": _truncate_any(s.get("service"), 64),
                    "src_host": _truncate_any(s.get("src_host"), 64),
                    "dst_port": _truncate_any(s.get("dst_port"), 32),
                    "attack_type": _truncate_any(s.get("attack_type"), 64),
                    "logdata": _truncate_any(s.get("logdata"), 400),
                    "details": _truncate_any(s.get("details"), 400),
                }
            )
        payload["event_samples"] = slim
    else:
        payload["event_samples"] = []

    return payload


def _parse_time(value: str | None):
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


def _aggregate_jsonl(source_path: Path, max_events: int | None = None):
    total = 0

    logtype_counter = Counter()
    src_counter = Counter()
    dst_port_counter = Counter()
    service_counter = Counter()

    usernames = Counter()
    paths = Counter()
    useragents = Counter()

    samples: list[dict] = []
    seen_events = 0

    first_ts = None
    last_ts = None

    def _bump(counter: Counter, value):
        if value is None:
            return
        s = str(value).strip()
        if not s:
            return
        counter[s] += 1

    def _parse_event(line: str):
        line = (line or "").strip()
        if not line:
            return None
        try:
            evt = json.loads(line)
        except Exception:
            return None
        return evt if isinstance(evt, dict) else None

    def _event_timestamp(evt: dict):
        return (
            _parse_time(evt.get("local_time_adjusted"))
            or _parse_time(evt.get("local_time"))
            or _parse_time(evt.get("utc_time"))
        )

    def _add_sample(evt: dict):
        sample = {
            "timestamp": evt.get("timestamp")
            or evt.get("local_time_adjusted")
            or evt.get("utc_time")
            or evt.get("local_time"),
            "logtype": evt.get("logtype"),
            "service": evt.get("service"),
            "src_host": evt.get("src_host"),
            "src_port": evt.get("src_port"),
            "dst_host": evt.get("dst_host"),
            "dst_port": evt.get("dst_port"),
            "severity": evt.get("severity"),
            "attack_type": evt.get("attack_type"),
            "logdata": evt.get("logdata"),
            "details": evt.get("details"),
        }

        try:
            encoded = json.dumps(sample, ensure_ascii=False)
            if len(encoded) > 1500:
                sample = {
                    "timestamp": sample.get("timestamp"),
                    "logtype": sample.get("logtype"),
                    "service": sample.get("service"),
                    "src_host": sample.get("src_host"),
                    "dst_port": sample.get("dst_port"),
                    "attack_type": sample.get("attack_type"),
                    "logdata": sample.get("logdata"),
                }
        except Exception:
            sample = {
                "timestamp": evt.get("timestamp"),
                "logtype": evt.get("logtype"),
                "service": evt.get("service"),
                "src_host": evt.get("src_host"),
                "dst_port": evt.get("dst_port"),
                "attack_type": evt.get("attack_type"),
            }

        nonlocal seen_events
        seen_events += 1
        if len(samples) < _SAMPLE_LIMIT:
            samples.append(sample)
            return

        j = random.randrange(seen_events)
        if j < _SAMPLE_LIMIT:
            samples[j] = sample

    total_bytes = 0
    try:
        total_bytes = source_path.stat().st_size
    except Exception:
        total_bytes = 0

    if _is_interactive():
        try:
            mb = total_bytes / (1024 * 1024)
            print(f"Parsing log: {mb:.1f} MB", flush=True)
        except Exception:
            pass

    processed = 0
    bytes_read = 0
    last_progress = 0.0
    for line, nbytes in _iter_jsonl_lines_stream(source_path):
        if max_events is not None and total >= max_events:
            break

        evt = _parse_event(line)
        if evt is None:
            continue

        total += 1
        processed += 1
        bytes_read += nbytes

        _bump(logtype_counter, evt.get("logtype"))
        _bump(src_counter, evt.get("src_host"))

        dst_port = evt.get("dst_port")
        if dst_port not in (None, -1, "-1"):
            _bump(dst_port_counter, dst_port)
        _bump(service_counter, evt.get("service"))

        logdata = evt.get("logdata")
        if isinstance(logdata, dict):
            _bump(usernames, logdata.get("USERNAME"))
            _bump(paths, logdata.get("PATH"))
            ua = logdata.get("USERAGENT")
            if ua:
                useragents[str(ua)[:200]] += 1

        ts = _event_timestamp(evt)
        if ts is not None:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts

        _add_sample(evt)

        if _is_interactive():
            now = time.monotonic()
            if processed == 1 or (now - last_progress) >= 0.25 or processed % 2500 == 0:
                last_progress = now
                if total_bytes > 0:
                    pct = (bytes_read / total_bytes) * 100
                    print(
                        f"Parsing log: {bytes_read}/{total_bytes} bytes ({pct:5.1f}%)",
                        end="\r",
                        flush=True,
                    )
                else:
                    print(f"Parsing log: {processed} events", end="\r", flush=True)

    if _is_interactive():
        print("".ljust(80), end="\r", flush=True)
        print(f"Parsing done: {processed} events", flush=True)

    def _as_items(counter: Counter, limit: int):
        return [{"value": k, "count": v} for (k, v) in counter.most_common(limit)]

    return {
        "total_events": total,
        "time_range": {
            "first": first_ts.isoformat() if first_ts else None,
            "last": last_ts.isoformat() if last_ts else None,
        },
        "top_logtypes": _as_items(logtype_counter, 15),
        "top_sources": _as_items(src_counter, 30),
        "top_dst_ports": _as_items(dst_port_counter, 15),
        "top_services": _as_items(service_counter, 15),
        "top_usernames": _as_items(usernames, 20),
        "top_paths": _as_items(paths, 20),
        "top_useragents": _as_items(useragents, 10),
        "event_samples": samples,
        "schema_notes": {
            "top_logtypes": "Tipos de evento (evt.logtype).",
            "top_sources": "Valores de evt.src_host (podem ser IPs, vazios ou outros identificadores dependendo do evento).",
            "event_samples": "Amostra limitada de eventos brutos (campos principais) para que a IA infira técnicas e recomendações sem heurísticas no código.",
        },
    }


def _prompt_report(aggregates: dict) -> dict:
    system_prompt = (
        "Você é um analista sênior de cibersegurança e GRC (Governança, Risco e Compliance).\n"
        "Seu objetivo é transformar um agregado estatístico de eventos de honeypot em um relatório EXECUTIVO e TÉCNICO, útil e acionável.\n\n"
        "REGRAS OBRIGATÓRIAS:\n"
        "- Saída SOMENTE em Markdown (sem JSON, sem blocos de código).\n"
        "- Não invente fatos. Todas as afirmações devem ser baseadas EXCLUSIVAMENTE nos dados fornecidos.\n"
        "- Sempre que fizer uma afirmação, cite a evidência usando os campos e contagens do agregado (ex.: top_dst_ports, top_services, top_sources, total_events, time_range).\n"
        "- Se algo não estiver nos dados, escreva explicitamente: \"Não é possível determinar a partir do agregado\".\n"
        "- Evite frases genéricas como \"implementar segurança\". Seja específico: controles, configurações, playbooks e políticas.\n"
        "- Priorize por impacto e frequência (use as contagens para justificar).\n"
        "- Use linguagem em português, profissional, objetiva.\n"
        "- Quando referenciar top_* do agregado, sempre escreva no formato: valor (contagem).\n"
        "- IMPORTANTE: 'count' significa NÚMERO DE EVENTOS, não número de IPs. Nunca escreva 'IPs' ao lado de contagens.\n"
        "- Inferir técnicas a partir de evidências em event_samples (campos como logdata, details, dst_port, service, attack_type).\n"
        "- Não assuma que um serviço específico existe: use apenas o que aparecer nos dados.\n"
        "- NÃO repita frases ou itens. Não copie/cole variações do mesmo bullet.\n"
        "- Quando eu pedir uma tabela, entregue uma tabela Markdown válida.\n"
    )

    user_prompt = (
        "Gere um relatório de segurança e compliance a partir do agregado abaixo.\n\n"
        "FORMATO OBRIGATÓRIO DO RELATÓRIO (use exatamente estas seções e nesta ordem):\n\n"
        "# Relatório de Segurança (Honeypot Deceptgold)\n\n"
        "## 1) Sumário Executivo (2–6 bullets)\n"
        "- Volume total de eventos, período analisado e 3 achados principais (com evidência numérica).\n"
        "- 3 riscos priorizados com justificativa (impacto x frequência).\n"
        "- 3 próximos passos imediatos para endurecer o host (hardening) e melhorar detecção (EXATAMENTE 3 bullets, cada um com evidência).\n\n"
        "## 2) Escopo e Evidências\n"
        "Inclua as tabelas abaixo (todas em Markdown).\n\n"
        "Tabela A — Escopo\n"
        "| Item | Valor |\n"
        "|---|---|\n"
        "| Total de eventos | <total_events> |\n"
        "| Janela de tempo | <time_range.first> até <time_range.last> |\n\n"
        "Tabela B — Top Estatísticas (máx. 10 linhas por tabela; formato: value (count))\n"
        "Origens (top_sources)\n"
        "| Origem | Eventos |\n"
        "|---|---:|\n"
        "| <value> | <count> |\n\n"
        "Portas destino (top_dst_ports)\n"
        "| Porta | Eventos |\n"
        "|---:|---:|\n"
        "| <value> | <count> |\n\n"
        "Serviços (top_services)\n"
        "| Serviço | Eventos |\n"
        "|---|---:|\n"
        "| <value> | <count> |\n\n"
        "Logtypes (top_logtypes)\n"
        "| Logtype | Eventos |\n"
        "|---|---:|\n"
        "| <value> | <count> |\n\n"
        "Evidências textuais: cite 3 a 8 eventos de event_samples (trechos relevantes) e diga por que são importantes.\n"
        "Observação: liste exatamente o que existe no agregado; não crie campos novos.\n\n"
        "## 3) Principais Vetores e Técnicas Prováveis (mapeamento)\n"
        "Para cada item:\n"
        "- Evidência: cite portas/serviços/logtypes e contagens.\n"
        "- Interpretação: o que isso sugere (ex.: brute force, enumeração, exploração web, varredura).\n"
        "- Confiança: alta/média/baixa (alta quando há sinais fortes no agregado).\n"
        "Inclua no máximo 5 vetores, priorizados por evidência. Não repita vetores equivalentes.\n\n"
        "## 4) Riscos e Impactos (orientado a compliance)\n"
        "Entregue uma tabela (5 a 8 linhas):\n"
        "| Risco | Evidência (campo + value + count) | Impacto | Probabilidade | Severidade |\n"
        "|---|---|---|---|---|\n"
        "| <texto> | <texto> | <texto> | alta/média/baixa | alta/média/baixa |\n\n"
        "## 5) Remediações Priorizadas (plano de ação)\n"
        "Crie uma tabela Markdown com colunas:\n"
        "- Prioridade (P0/P1/P2)\n"
        "- Ação (bem específica)\n"
        "- Alvo (serviço/porta)\n"
        "- Evidência (qual dado justificou)\n"
        "- Esforço (baixo/médio/alto)\n"
        "- Resultado esperado (mensurável)\n\n"
        "Regras para esta tabela:\n"
        "- 8 a 12 linhas no total.\n"
        "- Nenhuma ação pode ser genérica. Especifique o que mudar e onde (ex.: sshd_config, firewall, WAF, rate limit, IDS/SIEM).\n"
        "- Não repetir ações iguais com texto diferente.\n\n"
        "## 6) Detecções Recomendadas (regras e alertas)\n"
        "Crie uma tabela com 6 a 10 regras objetivas (baseadas em evidência).\n"
        "| Regra/Detecção | Fonte (logs/campo) | Condição | Severidade | Evidência |\n"
        "|---|---|---|---|---|\n"
        "| <texto> | <texto> | <texto> | alta/média/baixa | <texto> |\n\n"
        "## 7) Controles de Compliance (mapeamento)\n"
        "Mapeie recomendações para frameworks (sem inventar auditoria):\n"
        "- ISO 27001: A.5, A.8, A.12, A.13, A.16 (cite o porquê)\n"
        "- NIST CSF 2.0: Identify/Protect/Detect/Respond/Recover (cite o porquê)\n"
        "- CIS Controls v8: 4, 8, 12, 13, 16 (cite o porquê)\n"
        "Se não houver evidência suficiente para mapear algo, diga isso.\n\n"
        "## 8) MITRE ATT&CK (técnicas prováveis)\n"
        "Entregue uma tabela (3 a 8 linhas):\n"
        "| Técnica (ID + nome) | Evidência (event_samples + top_*) | Confiança | Mitigação prática |\n"
        "|---|---|---|---|\n"
        "| <texto> | <texto> | alta/média/baixa | <texto> |\n\n"
        "## 9) Lacunas e Próximos Passos (para melhorar a detecção e o host)\n"
        "- O que o agregado não permite concluir.\n"
        "- Quais campos/dados adicionais deveriam ser coletados.\n"
        "- Sugestão de alertas (regras simples) derivadas dos top ports/sources/services.\n\n"
        "DADOS (AGREGADO JSON):\n"
        f"{json.dumps(_build_prompt_payload(aggregates, sample_limit=12), ensure_ascii=False)}\n"
    )

    return {"system": system_prompt, "user": user_prompt}


def _write_pdf(dest: Path, markdown_text: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    import re

    doc = SimpleDocTemplate(str(dest), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    styles.add(ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold'))

    def md_to_pdf_content(text):
        lines = text.splitlines()
        in_table = False
        table_data = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_table:
                    _add_table(table_data)
                    in_table = False
                    table_data = []
                story.append(Spacer(1, 0.1 * inch))
                continue

            # Tables
            if line.startswith('|'):
                if '---|' in line or '|---' in line:
                    continue
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if cells:
                    table_data.append([Paragraph(c, styles['Normal']) for c in cells])
                    in_table = True
                continue
            elif in_table:
                _add_table(table_data)
                in_table = False
                table_data = []

            # Headers
            if line.startswith('# '):
                story.append(Paragraph(line[2:], styles['Title']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading2']))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading3']))
            # Lists
            elif line.startswith('- ') or line.startswith('* '):
                clean_line = _process_inline(line[2:])
                story.append(Paragraph(f"• {clean_line}", styles['Normal']))
            # Normal text
            else:
                story.append(Paragraph(_process_inline(line), styles['Normal']))
            
        if in_table:
            _add_table(table_data)

    def _add_table(data):
        if not data: return
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

    def _process_inline(text):
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # Convert *italic* to <i>italic</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        return text

    md_to_pdf_content(markdown_text)
    doc.build(story)


@reports_app.command(
    name="ai-report",
    help=(
        "Generate an AI report from a JSONL file produced by Deceptgold.\n\n"
        "Required arguments (key=value):\n"
        "  dest=/path/to/output            Destination path (required). Extension should match format.\n"
        "  format=markdown|pdf             Output format (required)\n"
        "\nOptional arguments (key=value):\n"
        "  model=<key>                     Model key to use (same keys shown in 'deceptgold ai install-model').\n"
        "                                 If not provided: uses the only installed model, or prompts if multiple are installed.\n"
        "                                 You can also set DECEPTGOLD_AI_MODEL=<key>.\n"
    ),
)
def ai_report(*args):
    from deceptgold.helper.helper import parse_args

    parsed = parse_args(args)

    dest = parsed.get("dest")
    fmt = (parsed.get("format") or "").strip().lower()
    model_key_arg = (parsed.get("model") or "").strip()

    allowed_keys = {"dest", "format", "model"}
    unknown = sorted(set(parsed.keys()) - allowed_keys)
    if unknown:
        print(f"Unknown arguments: {', '.join(unknown)}")
        print("Usage: deceptgold reports ai-report dest=/path/to/output format=markdown|pdf [model=<key>]")
        raise SystemExit(1)

    if not dest or fmt not in {"markdown", "pdf"}:
        print("Usage: deceptgold reports ai-report dest=/path/to/output format=markdown|pdf [model=<key>]")
        raise SystemExit(1)

    source_path = Path(get_temp_log_path(NAME_FILE_LOG))
    dest_path = Path(str(dest)).expanduser()

    if not source_path.exists():
        print(f"Source file not found: {source_path}")
        raise SystemExit(1)

    model_key = model_key_arg
    if not model_key:
        installed_models = list_installed_models() or []
        if len(installed_models) == 1:
            model_key = str(installed_models[0].get("key") or "default").strip() or "default"
        elif len(installed_models) > 1 and _is_interactive():
            print("Select installed AI model to generate the report:")
            key_w = 0
            fname_w = 0
            for m in installed_models:
                key_w = max(key_w, len(str(m.get("key") or "").strip()))
                fname_w = max(fname_w, len(str(m.get("filename") or "").strip()))
            for i, m in enumerate(installed_models, start=1):
                k = str(m.get("key") or "").strip()
                fn = str(m.get("filename") or "").strip()
                print(f"  {i:>2}) {k:<{key_w}}  {fn:<{fname_w}}")
            print("Choose [1]: ", end="", flush=True)
            raw = (sys.stdin.readline() or "").strip()
            if not raw:
                chosen_idx = 1
            else:
                try:
                    chosen_idx = int(raw)
                except Exception:
                    chosen_idx = 1
            if chosen_idx < 1 or chosen_idx > len(installed_models):
                chosen_idx = 1
            model_key = str(installed_models[chosen_idx - 1].get("key") or "default").strip() or "default"
        else:
            model_key = (os.environ.get("DECEPTGOLD_AI_MODEL") or "default").strip() or "default"

    installed = ensure_model_installed(model_key, interactive=True)
    if not installed:
        print(
            "AI-Report requires a local GGUF model.\n\n"
            "This model is necessary to generate compliance-oriented reports with prioritized risks and remediations.\n"
            "If you declined the download prompt, re-run the command and accept the download."
        )
        raise SystemExit(1)

    model_path = str(installed)

    aggregates = _aggregate_jsonl(source_path, max_events=None)

    llm = _load_llm(model_path)

    max_tokens = 1200
    temperature = 0.2

    prompts = _prompt_report(aggregates)
    system_prompt = str(prompts.get("system") or "")
    user_prompt = str(prompts.get("user") or "")

    def _generate_with_progress(_system_prompt: str, _user_prompt: str) -> str:
        interactive = _is_interactive()

        if hasattr(llm, "create_chat_completion"):
            if interactive:
                try:
                    chunks = llm.create_chat_completion(
                        messages=[
                            {"role": "system", "content": _system_prompt},
                            {"role": "user", "content": _user_prompt},
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                    )

                    spinner = itertools.cycle("|/-\\")
                    last = time.monotonic()
                    buf: list[str] = []
                    emitted = 0
                    print("Generating report...", flush=True)
                    for c in chunks:
                        delta = (
                            c.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            or ""
                        )
                        if delta:
                            buf.append(delta)
                            emitted += len(delta)

                        now = time.monotonic()
                        if (now - last) >= 0.25:
                            last = now
                            print(
                                f"Generating report {next(spinner)} ({emitted} chars)",
                                end="\r",
                                flush=True,
                            )

                    print("".ljust(80), end="\r", flush=True)
                    return "".join(buf).strip()
                except TypeError:
                    pass
                except Exception:
                    pass

            out = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": _system_prompt},
                    {"role": "user", "content": _user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return (
                out.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
            ).strip()

        prompt = _system_prompt + "\n\n" + _user_prompt
        if interactive:
            try:
                chunks = llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )
                spinner = itertools.cycle("|/-\\")
                last = time.monotonic()
                buf: list[str] = []
                emitted = 0
                print("Generating report...", flush=True)
                for c in chunks:
                    txt = (c.get("choices", [{}])[0].get("text", "") or "")
                    if txt:
                        buf.append(txt)
                        emitted += len(txt)

                    now = time.monotonic()
                    if (now - last) >= 0.25:
                        last = now
                        print(
                            f"Generating report {next(spinner)} ({emitted} chars)",
                            end="\r",
                            flush=True,
                        )

                print("".ljust(80), end="\r", flush=True)
                return "".join(buf).strip()
            except TypeError:
                pass
            except Exception:
                pass

        out = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return "".join(out.get("choices", [{}])[0].get("text", "") or "").strip()

    report_md = ""
    try:
        report_md = _generate_with_progress(system_prompt, user_prompt)
    except ValueError as e:
        msg = str(e)
        if "exceed context window" not in msg:
            raise

        reduced_user_prompt = (
            user_prompt.split("DADOS (AGREGADO JSON):", 1)[0]
            + "DADOS (AGREGADO JSON):\n"
            + json.dumps(_build_prompt_payload(aggregates, sample_limit=5), ensure_ascii=False)
            + "\n"
        )

        report_md = _generate_with_progress(system_prompt, reduced_user_prompt)

    def _needs_continuation(text: str) -> bool:
        if not text:
            return True
        if "## 9)" in text:
            return False
        return True

    if _needs_continuation(report_md):
        continuation_prompt = (
            "O relatório ficou incompleto. Continue exatamente de onde parou, "
            "mantendo o mesmo formato e sem repetir seções já escritas. "
            "Finalize todas as seções restantes até a seção 9." 
        )
        for _ in range(2):
            extra = _generate_with_progress(system_prompt, continuation_prompt)
            if extra:
                report_md = (report_md.rstrip() + "\n\n" + extra.lstrip()).strip()
            if not _needs_continuation(report_md):
                break

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "markdown":
        dest_path.write_text(report_md + "\n", encoding="utf-8")
        print(f"Report written to: {dest_path}")
        return

    if fmt == "pdf":
        _write_pdf(dest_path, report_md)
        print(f"Report written to: {dest_path}")
        return
