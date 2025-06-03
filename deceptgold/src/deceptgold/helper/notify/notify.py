from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.configuration.opecanary import get_config_value

def check_send_notify(message):
    notification_telegram = True
    if notification_telegram:
        message = f"{get_config_value('device', 'node_id')} - {message}"
        send_message_telegram(message)
