from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.configuration.opecanary import get_config_value
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.fingerprint import get_machine_fingerprint
from deceptgold.helper.notify.webhook import send_message_webhook

def check_send_notify(message):
    fingerprint = get_machine_fingerprint()
    message = f"{get_config_value('device', 'node_id')} - {message}"

    try:
        send_message_telegram(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message telegram: {e}")

    try:
        send_message_webhook(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message webhook: {e}")

