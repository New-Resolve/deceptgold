from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.configuration.secrets import get_secret
from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.helper.fingerprint import get_ip_public, get_name_user

try:
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None

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
            send_message_telegram(message_send=f'Software v{installed_version} is installed in {get_ip_public()} to user: {get_name_user()}',
                                  chat_id=get_secret("TELEMETRY_TELEGRAM_CHAT_ID", default=None))