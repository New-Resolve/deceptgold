from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.helper.fingerprint import get_ip_public, get_name_user

def exec_telemetry():
    first_init = get_config(key='initialize', module_name_honeypot='software', passwd='passwd', default=None)
    if not first_init:
        update_config('initialize', value='yes', module_name='software', passwd='passwd')
        if not input("Do you agree to send anonymous usage statistics? (Y/n): ").strip().lower() in ("n", "no"):
            send_message_telegram(message_send=f'Software is installed in {get_ip_public()} to user: {get_name_user()}',
                                  chat_id='845496816')