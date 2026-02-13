import json
import os
import sys
from pathlib import Path

import httpx


def _user_models_dir() -> Path:
    return Path.home() / ".deceptgold" / "models"


def _embedded_models_dir() -> Path:
    return (Path(__file__).resolve().parent.parent / "resources" / "models").resolve()


def _manifest_path() -> Path:
    return _embedded_models_dir() / "model_manifest.json"


def _load_manifest() -> dict:
    path = _manifest_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _installed_models(manifest: dict) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not isinstance(manifest, dict):
        return out

    for k, v in manifest.items():
        if not isinstance(k, str):
            continue
        if not isinstance(v, dict):
            continue
        filename = str(v.get("filename") or "").strip()
        if not filename:
            continue
        p = _user_models_dir() / filename
        if p.exists():
            out.append((k, p))

    return out


def list_installed_models() -> list[dict]:
    return [m for m in (list_available_models() or []) if bool(m.get("installed"))]


def list_available_models() -> list[dict]:
    manifest = _load_manifest() or {}

    keys = [k for k in manifest.keys() if isinstance(k, str) and k.strip()]
    if "default" not in keys:
        keys = ["default", *keys]

    ordered: list[str] = []
    if "default" in keys:
        ordered.append("default")
    for k in sorted(set(keys)):
        if k != "default":
            ordered.append(k)

    out: list[dict] = []
    for k in ordered:
        info = get_model_info(k)
        filename = str(info.get("filename") or "").strip()
        url = str(info.get("url") or "").strip()
        path = _user_models_dir() / filename if filename else Path("")
        out.append(
            {
                "key": k,
                "filename": filename,
                "url": url,
                "path": path,
                "installed": bool(filename and path.exists()),
            }
        )
    return out


def get_model_info(model_key: str = "default") -> dict:
    manifest = _load_manifest()
    entry = manifest.get(model_key) or {}

    filename = str(entry.get("filename") or "").strip()
    url = str(entry.get("url") or "").strip()

    if model_key == "default":
        if not filename:
            filename = "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
        if not url:
            url = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"

    return {"filename": filename, "url": url, "key": model_key}


def get_default_model_info() -> dict:
    return get_model_info("default")


def get_default_model_target_path() -> Path:
    info = get_default_model_info()
    filename = (info.get("filename") or "").strip()
    if not filename:
        return Path("")
    return _user_models_dir() / filename


def is_interactive() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def ensure_default_model_installed(interactive: bool = True) -> Path:
    """Ensure the default GGUF model exists in ~/.deceptgold/models.

    If missing and interactive=True, asks the user whether to download it.
    Returns the model path if installed/existing, otherwise an empty Path.
    """

    manifest = _load_manifest()
    installed = _installed_models(manifest)
    if installed:
        for k, p in installed:
            if k == "default":
                return p
        return installed[0][1]

    if not interactive or not is_interactive():
        return ensure_model_installed("default", interactive=interactive)

    env_key = (os.environ.get("DECEPTGOLD_AI_MODEL") or "").strip()
    if env_key:
        return ensure_model_installed(env_key, interactive=interactive)

    manifest = manifest or _load_manifest()
    keys = [k for k in manifest.keys() if isinstance(k, str) and k.strip()]
    if len(keys) <= 1:
        return ensure_model_installed("default", interactive=interactive)

    ordered = []
    if "default" in manifest:
        ordered.append("default")
    for k in sorted(keys):
        if k != "default":
            ordered.append(k)

    print("Select AI model to download/install:")
    for i, k in enumerate(ordered, start=1):
        info = get_model_info(k)
        filename = str(info.get("filename") or "").strip()
        print(f"  {i}) {k} - {filename}")
    print("Choose [1]: ", end="", flush=True)
    raw = (sys.stdin.readline() or "").strip()
    if not raw:
        chosen = ordered[0]
    else:
        try:
            idx = int(raw)
            chosen = ordered[idx - 1] if 1 <= idx <= len(ordered) else ordered[0]
        except Exception:
            chosen = ordered[0]

    return ensure_model_installed(chosen, interactive=interactive)


def install_model_by_key(model_key: str, interactive: bool = True, assume_yes: bool = False) -> Path:
    info = get_model_info(model_key)
    filename = (info.get("filename") or "").strip()
    url = (info.get("url") or "").strip()

    if not filename:
        return Path("")

    target = _user_models_dir() / filename
    if target.exists():
        return target

    if not url:
        return Path("")

    if not interactive or not is_interactive():
        return Path("")

    if not assume_yes:
        print(
            "Deceptgold AI Model is not installed.\n"
            "This model is required to generate AI-Reports (compliance-oriented summaries and remediation recommendations).\n\n"
            f"Model: {filename}\n"
            f"Source: {url}\n\n"
            "Do you want to download and install it now? [Y/n]: ",
            end="",
            flush=True,
        )

        ans = (sys.stdin.readline() or "").strip().lower()
        if ans in {"n", "no"}:
            manifest = _load_manifest()
            installed = _installed_models(manifest)
            if installed:
                for k, p in installed:
                    if k == "default":
                        return p
                return installed[0][1]
            return Path("")

    _user_models_dir().mkdir(parents=True, exist_ok=True)

    tmp = target.with_suffix(target.suffix + ".part")

    with httpx.stream("GET", url, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        total = None
        try:
            if r.headers.get("Content-Length"):
                total = int(r.headers["Content-Length"])
        except Exception:
            total = None

        downloaded = 0
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and is_interactive():
                        pct = (downloaded / total) * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        print(
                            f"Downloading model: {pct:5.1f}% ({mb_done:.1f}/{mb_total:.1f} MB)",
                            end="\r",
                            flush=True,
                        )
                    elif is_interactive():
                        mb_done = downloaded / (1024 * 1024)
                        print(
                            f"Downloading model: {mb_done:.1f} MB", end="\r", flush=True
                        )

        if is_interactive():
            print("".ljust(80), end="\r", flush=True)

    tmp.replace(target)
    return target


def ensure_model_installed(model_key: str, interactive: bool = True) -> Path:
    return install_model_by_key(model_key, interactive=interactive, assume_yes=False)
