from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.configuration.opecanary import get_config_value
from deceptgold.helper.fingerprint import get_machine_fingerprint
from deceptgold.helper.notify.webhook import send_message_custom_webhook
from deceptgold.helper.notify.slack import send_message_webhook_slack
from deceptgold.helper.notify.discord import send_message_webhook_discord


def check_send_notify(message):
    fingerprint = get_machine_fingerprint()
    message = f"{get_config_value('device', 'node_id')} - {message}"

    try:
        send_message_telegram(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message telegram: {e}")

    try:
        send_message_custom_webhook(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message custom webhook: {e}")

    try:
        send_message_webhook_slack(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message slack webhook: {e}")

    try:
        send_message_webhook_discord(message, fingerprint)
    except Exception as e:
        raise Exception(f"Error in send message discord webhook: {e}")
