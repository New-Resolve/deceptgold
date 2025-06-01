from deceptgold.helper.notify.telegram import send_message_telegram
from deceptgold.configuration.opecanary import NODE_ID

def check_send_notify(message):
    notification_telegram = True
    if notification_telegram:
        message = f"{NODE_ID} - {message}"
        send_message_telegram(message)
