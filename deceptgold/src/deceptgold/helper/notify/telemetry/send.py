from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.configuration.secrets import get_secret
from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.helper.fingerprint import get_ip_public, get_name_user

import platform

try:
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None


def _get_ai_model_info() -> str:
    """Get information about installed AI models"""
    try:
        from deceptgold.helper.ai_model import list_installed_models, get_preferred_model_key
        
        installed_models = list_installed_models()
        if not installed_models:
            return "None installed"
        
        preferred_key = get_preferred_model_key()
        
        # Build model info string
        model_names = []
        for model in installed_models:
            key = model.get("key", "unknown").upper()
            if key == preferred_key.upper():
                model_names.append(f"{key} (preferred)")
            else:
                model_names.append(key)
        
        if len(model_names) == 1:
            return model_names[0]
        else:
            return f"{len(model_names)} models: {', '.join(model_names)}"
            
    except Exception:
        return "Unknown"

def exec_telemetry():
    try:
        if _pkg_version is not None:
            installed_version = _pkg_version("deceptgold")
        else:
            raise RuntimeError("importlib.metadata unavailable")
    except Exception:
        try:
            from deceptgold import __version__ as installed_version
        except Exception:
            installed_version = "unknown"

    first_init = get_config(key='initialize', module_name_honeypot='software', passwd='passwd', default=None)
    if not first_init:
        update_config('initialize', value='yes', module_name='software', passwd='passwd')
        if not input("Do you agree to send anonymous usage statistics? (Y/n): ").strip().lower() in ("n", "no"):
            # Get AI model information
            ai_model_info = _get_ai_model_info()
            
            message = (
                f"*Anonymous statistics ({installed_version})*\n"                
                f"- *User:* `{get_name_user()}`\n"
                f"- *Public IP:* `{get_ip_public()}`\n"
                f"- *OS:* `{platform.system()} {platform.release()}`\n"
                f"- *Platform:* `{platform.platform()}`\n"
                f"- *Arch:* `{platform.machine()}`\n"
                f"- *Python:* `{platform.python_version()}`\n"
                f"- *AI Model:* `{ai_model_info}`"
            )
            send_message_telegram(
                message_send=message,
                chat_id=get_secret("TELEMETRY_TELEGRAM_CHAT_ID", default=None),
                parse_mode="Markdown",
            )