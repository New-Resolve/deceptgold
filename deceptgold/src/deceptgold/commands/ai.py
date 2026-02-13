import json
import time
import logging
import shutil
import os
import subprocess
import sys
import psutil
import platform
from pathlib import Path

from cyclopts import App

from deceptgold.helper.helper import parse_args, get_temp_log_path, NAME_FILE_LOG
from deceptgold.helper.helper import NAME_FILE_PID
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.ai_model import list_available_models, install_model_by_key, is_interactive


logger = logging.getLogger(__name__)

ai_app = App(name="ai", help="Local AI agent commands")


def _user_models_dir() -> Path:
    return Path.home() / ".deceptgold" / "models"


def _embedded_models_dir() -> Path:
    return (Path(__file__).resolve().parent.parent / "resources" / "models").resolve()

def _find_model_path(override: str | None = None) -> str:
    if override:
        return str(override)

    return ""


def _iter_jsonl_follow(
    path: str,
    sleep_s: float = 0.2,
    show_wait_notice: bool = False,
):
    log_path = Path(path)
    did_notice = False

    while True:
        if not log_path.exists():
            if show_wait_notice and not did_notice:
                print(
                    "AI log follower is waiting for the honeypot log to appear.\n\n"
                    "What this command does:\n"
                    "  - It tails the honeypot JSONL log file and enriches events in real time.\n"
                    "  - When LLM is enabled, it also generates an AI analysis per event.\n\n"
                    "Why nothing is showing yet:\n"
                    "  - The log file does not exist yet, which usually means the honeypot is not running.\n\n"
                    "What you need to do:\n"
                    "  - Start the honeypot/service, then generate traffic (or wait for hits).\n"
                    "  - As soon as the honeypot creates the log file, this command will start streaming events automatically.\n\n"
                    f"Waiting for: {log_path}"
                )
                did_notice = True

            time.sleep(sleep_s)
            continue

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        if not log_path.exists():
                            break
                        time.sleep(sleep_s)
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    yield line
        except FileNotFoundError:
            time.sleep(sleep_s)
            continue
        except OSError:
            time.sleep(sleep_s)
            continue


def _service_pid_file() -> str:
    return get_temp_log_path(NAME_FILE_PID)


def _is_service_running() -> bool:
    pid_file = _service_pid_file()
    if not os.path.exists(pid_file):
        return False

    try:
        with open(pid_file, "r", encoding="utf-8") as f:
            pid_raw = f.read().strip()
        pid = int(pid_raw)
    except Exception:
        return False

    try:
        p = psutil.Process(pid)
        if not (p.is_running() and p.status() != psutil.STATUS_ZOMBIE):
            return False

        try:
            pid_mtime = os.path.getmtime(pid_file)
        except Exception:
            pid_mtime = None

        try:
            created = float(p.create_time())
        except Exception:
            created = None

        if pid_mtime is not None and created is not None:
            if created > (pid_mtime + 5.0):
                return False

        try:
            cmdline = " ".join(p.cmdline() or []).lower()
        except Exception:
            cmdline = ""

        if cmdline and ("deceptgold" in cmdline):
            return True

        return True
    except Exception:
        return False


def _prompt_yes_no(question: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    while True:
        ans = input(f"{question} {suffix} ").strip().lower()
        if not ans:
            return default_yes
        if ans in {"y", "yes", "s", "sim"}:
            return True
        if ans in {"n", "no", "nao", "não"}:
            return False


def _wallet_configured() -> bool:
    try:
        return get_config("user", "address", None) is not None
    except Exception:
        return False


def _start_service_daemon(force_no_wallet: bool = False) -> None:
    executable_path = str(Path(sys.executable))
    extra_args = ["force-no-wallet=true"] if force_no_wallet else []
    if "python" in os.path.basename(executable_path).lower():
        cmd = [executable_path, "-m", "deceptgold", "service", "start", *extra_args]
    else:
        cmd = [executable_path, "service", "start", *extra_args]

    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=(platform.system() != "Windows"),
    )


def _restart_service_daemon(force_no_wallet: bool = False) -> None:
    executable_path = str(Path(sys.executable))
    extra_args = ["force-no-wallet=true"] if force_no_wallet else []
    if "python" in os.path.basename(executable_path).lower():
        cmd = [executable_path, "-m", "deceptgold", "service", "restart", *extra_args]
    else:
        cmd = [executable_path, "service", "restart", *extra_args]

    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=(platform.system() != "Windows"),
    )


def _enrich_event(evt: dict) -> dict:
    logtype = evt.get("logtype")

    category = "unknown"
    risk = "low"

    if logtype == 1001:
        category = "service_info"
        risk = "low"
    elif logtype == 3000:
        category = "http_probe"
        risk = "low"
    elif logtype == 3001:
        category = "http_login_attempt"
        risk = "medium"
    elif logtype == 4000:
        category = "scan_or_bruteforce"
        risk = "medium"
    elif logtype == 5000:
        category = "web3_activity"
        risk = "medium"

    enriched = {
        "event": evt,
        "ai": {
            "category": category,
            "risk": risk,
        },
    }
    return enriched


def _should_process(enriched: dict, include_logtypes: set[int] | None) -> bool:
    evt = enriched.get("event", {})
    logtype = evt.get("logtype")

    if include_logtypes is not None:
        return logtype in include_logtypes

    return logtype not in {1001}


def _load_llm(model_path: str):
    from llama_cpp import Llama

    n_ctx = 2048
    n_threads = 0

    kwargs = {
        "model_path": model_path,
        "n_ctx": n_ctx,
        "verbose": False,
    }
    if n_threads > 0:
        kwargs["n_threads"] = n_threads

    return Llama(**kwargs)


def _llm_analyze(llm, enriched: dict) -> dict:
    max_tokens = 192
    temperature = 0.2

    evt = enriched.get("event", {})

    prompt = (
        "You are a cybersecurity analyst. Analyze the event below and output ONLY valid JSON with keys: "
        "summary, iocs, recommended_actions.\n\n"
        "Event JSON:\n"
        f"{json.dumps(evt, ensure_ascii=False)}\n"
    )

    out = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["\n\n"],
    )
    text = "".join(out.get("choices", [{}])[0].get("text", "") or "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {"summary": text, "iocs": [], "recommended_actions": []}


@ai_app.command(
    name="start",
    help=(
        "Start local AI agent that consumes the honeypot JSONL log and enriches events.\n\n"
        "Optional arguments (key=value):\n"
        "  log-file=/path/to/log           Source JSONL file (default: temp .deceptgold.log)\n"
        "  out-file=/path/to/out           Output JSONL file (default: disabled)\n"
        "  include-logtypes=3001,4000      Only process selected logtypes\n"
        "  llm=true|false                  Enable local LLM analysis (default: from config ai.enabled)\n"
        "  model=/path/to/model.gguf       Override config ai.model_path\n"
    ),
)
def start(*args):
    parsed_args = parse_args(args)

    log_file = parsed_args.get("log_file") or get_temp_log_path(NAME_FILE_LOG)
    out_file = parsed_args.get("out_file")

    include_logtypes = None
    include_raw = parsed_args.get("include_logtypes")
    if include_raw:
        try:
            include_logtypes = {int(x.strip()) for x in str(include_raw).split(",") if x.strip()}
        except Exception:
            include_logtypes = None

    llm_enabled = bool(parsed_args.get("llm", False))

    model_path = _find_model_path(parsed_args.get("model"))

    llm = None
    if llm_enabled:
        if not model_path:
            embedded = _embedded_models_dir()
            print(
                "Local AI is enabled, but no GGUF model was found.\n"
                "To generate AI reports, you must install a local model.\n\n"
                "Options:\n"
                "  1) Pass model=/path/to/model.gguf\n"
                "  2) Or install it to ~/.deceptgold/models manually\n\n"
                f"Embedded model directory (if shipped): {embedded}"
            )
            raise SystemExit(1)
        try:
            llm = _load_llm(model_path)
        except Exception as e:
            print(f"Unable to load local LLM. {e}")
            raise SystemExit(1)

    out_handle = None
    if out_file:
        out_handle = open(out_file, "a", encoding="utf-8")

    try:
        log_path = Path(log_file)
        service_running = _is_service_running()
        started_service = False
        force_no_wallet_choice: bool | None = None

        if not service_running:
            if _prompt_yes_no(
                "The Deceptgold honeypot/service does not appear to be running. Start it now?",
                default_yes=True,
            ):
                force_no_wallet = False
                if not _wallet_configured():
                    if force_no_wallet_choice is None:
                        force_no_wallet_choice = _prompt_yes_no(
                            "No public wallet address is configured. Start the service anyway using force-no-wallet=true?",
                            default_yes=True,
                        )
                    force_no_wallet = bool(force_no_wallet_choice)
                    if not force_no_wallet:
                        print(
                            "Service was not started. To configure your wallet address, run: user --my-address 0xYourPublicAddress\n"
                            "Or start the service manually with: service start force-no-wallet=true"
                        )
                if _wallet_configured() or force_no_wallet:
                    _start_service_daemon(force_no_wallet=force_no_wallet)
                    started_service = True
                    service_running = True
                    print(
                        "AI log follower is running and will start streaming as soon as the honeypot writes events.\n"
                        f"Waiting for: {log_path}"
                    )
            else:
                pass

        if started_service and (not log_path.exists()):
            wait_s = 4.0
            step_s = 0.2
            deadline = time.time() + wait_s
            while time.time() < deadline:
                if log_path.exists():
                    break
                time.sleep(step_s)

        if not log_path.exists():
            if service_running:
                if _prompt_yes_no(
                    "The honeypot/service seems to be running, but the log file is missing. Restart the service now to recreate the log file?",
                    default_yes=True,
                ):
                    force_no_wallet = False
                    if not _wallet_configured():
                        if force_no_wallet_choice is None:
                            force_no_wallet_choice = _prompt_yes_no(
                                "No public wallet address is configured. Restart the service anyway using force-no-wallet=true?",
                                default_yes=True,
                            )
                        force_no_wallet = bool(force_no_wallet_choice)
                        if not force_no_wallet:
                            print(
                                "Service was not restarted. To configure your wallet address, run: user --my-address 0xYourPublicAddress\n"
                                "Or restart the service manually with: service restart force-no-wallet=true"
                            )

                    if _wallet_configured() or force_no_wallet:
                        _restart_service_daemon(force_no_wallet=force_no_wallet)
                    print(f"Waiting for: {log_path}")
                else:
                    print(
                        "AI log follower is waiting for the honeypot log to appear.\n\n"
                        "The honeypot/service seems to be running, but the log file is not present yet.\n"
                        "If you deleted the log file while the service was running, the process may still be writing to the old file handle.\n"
                        "In that case, restart the service so it recreates the log file.\n\n"
                        f"Waiting for: {log_path}"
                    )
            else:
                print(
                    "AI log follower is waiting for the honeypot log to appear.\n\n"
                    "What this command does:\n"
                    "  - It tails the honeypot JSONL log file and enriches events in real time.\n"
                    "  - When LLM is enabled, it also generates an AI analysis per event.\n\n"
                    "Why nothing is showing yet:\n"
                    "  - The log file does not exist yet, which usually means the honeypot is not running.\n\n"
                    "What you need to do:\n"
                    "  - Start the honeypot/service, then generate traffic (or wait for hits).\n"
                    "  - As soon as the honeypot creates the log file, this command will start streaming events automatically.\n\n"
                    f"Waiting for: {log_path}"
                )

        for raw in _iter_jsonl_follow(log_file, show_wait_notice=False):
            try:
                evt = json.loads(raw)
            except Exception:
                continue

            enriched = _enrich_event(evt)
            if not _should_process(enriched, include_logtypes):
                continue

            if llm is not None:
                enriched["ai"]["analysis"] = _llm_analyze(llm, enriched)

            line = json.dumps(enriched, ensure_ascii=False)
            print(line)
            if out_handle is not None:
                out_handle.write(line + "\n")
                out_handle.flush()

    except KeyboardInterrupt:
        return
    finally:
        if out_handle is not None:
            out_handle.close()


@ai_app.command(
    name="install-model",
    help=(
        "List, download and install GGUF models for Deceptgold AI.\n\n"
        "These local models are required to generate AI reports (deceptgold reports ai-report).\n"
        "When multiple models are installed, you can choose which one to use via model=<key> or interactively.\n\n"
        "Optional arguments (key=value):\n"
        "  filename=model.gguf     Which embedded model file to install (default: ai.default_model_filename)\n"
        "  force=true|false        Overwrite if exists (default: false)\n"
    ),
)
def install_model(*args):
    parsed_args = parse_args(args)
    filename = str(parsed_args.get("filename") or "").strip()
    force = bool(parsed_args.get("force", False))

    if not filename:
        models = list_available_models()
        if not models:
            print(
                "No models are available for download/install.\n"
                "If you built from source, ensure deceptgold/resources/models/model_manifest.json is packaged.\n"
                "Or download a GGUF file manually and set ai.model_path."
            )
            raise SystemExit(1)

        print("Available AI models:")

        key_w = 0
        fname_w = 0
        for m in models:
            key_w = max(key_w, len(str(m.get("key") or "").strip()))
            fname_w = max(fname_w, len(str(m.get("filename") or "").strip()))
        key_w = max(key_w, len("key"))
        fname_w = max(fname_w, len("filename"))

        for i, m in enumerate(models, start=1):
            key = str(m.get("key") or "").strip()
            fname = str(m.get("filename") or "").strip()
            installed = bool(m.get("installed"))
            status = "[installed]" if installed else "[download]"
            print(f"  {i:>2}) {key:<{key_w}}  {fname:<{fname_w}}  {status}")

        if not is_interactive():
            print(
                "\nNon-interactive mode: choose a model by passing filename=<model.gguf> (embedded) or set DECEPTGOLD_AI_MODEL and run again interactively."
            )
            raise SystemExit(1)

        print("Choose [1]: ", end="", flush=True)
        raw = (sys.stdin.readline() or "").strip()
        if not raw:
            chosen_idx = 1
        else:
            try:
                chosen_idx = int(raw)
            except Exception:
                chosen_idx = 1

        if chosen_idx < 1 or chosen_idx > len(models):
            chosen_idx = 1

        chosen = models[chosen_idx - 1]
        chosen_key = str(chosen.get("key") or "default").strip() or "default"
        installed = bool(chosen.get("installed"))
        if installed:
            print(f"Model already installed: {chosen.get('path')}")
            return

        path = install_model_by_key(chosen_key, interactive=True, assume_yes=True)
        if not path:
            print("Unable to install the selected model.")
            raise SystemExit(1)

        print(
            f"Installed model to: {path}\n\n"
            "This local model enables AI reports. Generate a report with:\n"
            "  deceptgold reports ai-report source=/path/to/log.jsonl dest=/path/to/report.md format=markdown"
        )
        return

    src = _embedded_models_dir() / filename
    if not src.exists():
        print(
            "No embedded model found to install.\n\n"
            f"Expected file: {src}\n"
            "If you built from source, place the GGUF file in deceptgold/resources/models/ before packaging.\n"
            "If you are running from source without an embedded model, run: deceptgold ai install-model (interactive)\n"
            "Or download a GGUF file manually and set ai.model_path."
        )
        raise SystemExit(1)

    dst_dir = _user_models_dir()
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / filename

    if dst.exists() and not force:
        print(
            f"Model already installed: {dst}\n"
            "To overwrite, re-run with force=true."
        )
        return

    shutil.copy2(src, dst)
    print(
        f"Installed model to: {dst}\n\n"
        "This local model enables AI reports. Generate a report with:\n"
        "  deceptgold reports ai-report source=/path/to/log.jsonl dest=/path/to/report.md format=markdown"
    )
