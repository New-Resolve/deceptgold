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


def check_ai_model_available_silent() -> bool:
    """Silent check for AI models - no UI output"""
    try:
        from pathlib import Path
        
        # Check if we have a properly configured and usable model
        manifest = _load_manifest()
        installed = _installed_models(manifest)
        
        # If we have models from manifest, they are properly configured
        if installed:
            return True
            
        # The manifest system requires exact filename matches, but we might have
        # models that aren't properly registered. For AI start command, we need
        # models that can actually be loaded and used, not just any .gguf files.
        # Return False to force proper model installation/configuration.
        return False
        
    except Exception:
        return False


def list_installed_models() -> list[dict]:
    return [m for m in (list_available_models() or []) if bool(m.get("installed"))]


def list_available_models() -> list[dict]:
    manifest = _load_manifest() or {}

    keys = [k for k in manifest.keys() if isinstance(k, str) and k.strip()]
    
    # Order models with qwen first (as default), then others alphabetically
    ordered: list[str] = []
    if "qwen" in keys:
        ordered.append("qwen")
    for k in sorted(set(keys)):
        if k != "qwen":
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
                "specialty": info.get("specialty", ""),
                "use_case": info.get("use_case", ""),
                "description": info.get("description", ""),
            }
        )
    return out


def get_model_info(model_key: str = "qwen") -> dict:
    manifest = _load_manifest()
    entry = manifest.get(model_key) or {}

    filename = str(entry.get("filename") or "").strip()
    url = str(entry.get("url") or "").strip()
    specialty = str(entry.get("specialty") or "").strip()
    use_case = str(entry.get("use_case") or "").strip()
    description = str(entry.get("description") or "").strip()

    # Fallback for qwen model if not found in manifest
    if model_key == "qwen" and not filename:
        filename = "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
        url = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"

    return {
        "filename": filename, 
        "url": url, 
        "key": model_key,
        "specialty": specialty,
        "use_case": use_case,
        "description": description
    }


def get_default_model_info() -> dict:
    """Get info for the preferred AI model based on user selection or priority"""
    # First check if user has set a preferred model
    preferred_model = get_preferred_model_key()
    if preferred_model:
        return get_model_info(preferred_model)
    
    # Fallback to first installed model
    installed = list_installed_models()
    if installed:
        return get_model_info(installed[0]["key"])
    
    # Final fallback to qwen
    return get_model_info("qwen")


def get_default_model_target_path() -> Path:
    """Get path to the preferred AI model"""
    info = get_default_model_info()
    filename = (info.get("filename") or "").strip()
    if not filename:
        return Path("")
    
    model_path = _user_models_dir() / filename
    
    # If preferred model doesn't exist, try to find any installed model
    if not model_path.exists():
        installed = list_installed_models()
        for model in installed:
            if model.get("path") and Path(model["path"]).exists():
                return Path(model["path"])
    
    return model_path


def get_preferred_model_key() -> str:
    """Get the user's preferred AI model key from configuration"""
    try:
        from deceptgold.configuration.config_manager import get_config
        return get_config('ai_settings', 'preferred_model', '') or ''
    except Exception:
        return ''


def set_preferred_model(model_key: str) -> bool:
    """Set the user's preferred AI model"""
    try:
        from deceptgold.configuration.config_manager import update_config
        update_config('preferred_model', model_key, module_name='ai_settings')
        return True
    except Exception:
        return False


def list_installed_models_with_priority() -> list[dict]:
    """List installed models with preferred model first"""
    installed = list_installed_models()
    if not installed:
        return []
    
    preferred_key = get_preferred_model_key()
    if not preferred_key:
        return installed
    
    # Move preferred model to front
    preferred_models = [m for m in installed if m.get("key") == preferred_key]
    other_models = [m for m in installed if m.get("key") != preferred_key]
    
    return preferred_models + other_models


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

    # ALWAYS return empty path if no models installed - never show UI automatically
    return Path("")


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
    
    # Check if partial download exists and get resume position
    resume_pos = 0
    if tmp.exists():
        resume_pos = tmp.stat().st_size
        if is_interactive():
            mb_resume = resume_pos / (1024 * 1024)
            print(f"Resuming download from {mb_resume:.1f} MB...")

    # Set up headers for resume
    headers = {}
    if resume_pos > 0:
        headers["Range"] = f"bytes={resume_pos}-"

    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        
        # Handle partial content response
        if r.status_code == 206:  # Partial Content
            content_range = r.headers.get("Content-Range", "")
            if content_range.startswith("bytes"):
                # Extract total size from "bytes start-end/total"
                try:
                    total = int(content_range.split("/")[1])
                except Exception:
                    total = None
            else:
                total = None
        else:
            # Full download - server doesn't support resume or file doesn't exist
            if resume_pos > 0:
                if is_interactive():
                    print("Server doesn't support resume, starting from beginning...")
                resume_pos = 0
                tmp.unlink(missing_ok=True)  # Remove partial file
            
            total = None
            try:
                if r.headers.get("Content-Length"):
                    total = int(r.headers["Content-Length"])
            except Exception:
                total = None

        downloaded = resume_pos
        mode = "ab" if resume_pos > 0 else "wb"
        
        with tmp.open(mode) as f:
            for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and is_interactive():
                        pct = (downloaded / total) * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        print(
                            f"loading model: {pct:5.1f}% ({mb_done:.1f}/{mb_total:.1f} MB)",
                            end="\r",
                            flush=True,
                        )
                    elif is_interactive():
                        mb_done = downloaded / (1024 * 1024)
                        print(
                            f"loading model: {mb_done:.1f} MB", end="\r", flush=True
                        )

        if is_interactive():
            print("".ljust(80), end="\r", flush=True)

    tmp.replace(target)
    return target


def ensure_model_installed(model_key: str, interactive: bool = True) -> Path:
    return install_model_by_key(model_key, interactive=interactive, assume_yes=False)
