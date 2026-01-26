import uuid
import requests
import time

import qrcode_terminal

from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.configuration.secrets import get_secret
from deceptgold.helper.fingerprint import get_machine_fingerprint

BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN", default="")
NAME_BOT = 'DeceptGoldNotifybot'
LOCAL_TOKEN = str(uuid.uuid4())[-17:]

def generate_qrcode(token=LOCAL_TOKEN):
    url = f"https://t.me/{NAME_BOT}?start={token}"
    qrcode_terminal.draw(url)
    print(f"Scan the QRCode above to open in Telegram: {url} ⏳ Waiting for binding...")

def search_chat_id_by_token(token_local, fingerprint):
    offset = None
    try:
        if not BOT_TOKEN:
            print("Telegram bot token is not configured.")
            return False
        while True:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params={"offset": offset})
            updates = r.json()["result"]
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                txt = msg.get("text", "")
                if txt.startswith("/start ") and txt.split(" ")[1] == token_local:
                    chat_id = msg["chat"]["id"]
                    update_config('telegram', str(chat_id), module_name='webhook', passwd=fingerprint)
                    print("Telegram notifications have been successfully configured.")
                    return True
            time.sleep(2)
    except KeyboardInterrupt:
        print("Process interrupted by user. Telegram notifications have not been configured.")
        return False
    except Exception as e:
        print(f"Error: {e}")

def send_message_telegram(message_send, fingerprint=None, chat_id=None):
    if not BOT_TOKEN:
        return
    if not fingerprint:
        fingerprint = get_machine_fingerprint()
    if not chat_id:
        chat_id = get_config(module_name_honeypot='webhook', key='telegram', passwd=fingerprint, default=None)
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": int(chat_id),
        "text": message_send
    }
    r = requests.post(url, data=payload)
    if not r.ok:
        print("Error sending notification to telegram.")


def configure_telegram():
    if not BOT_TOKEN:
        print("Telegram bot token is not configured.")
        return
    fingerprint = get_machine_fingerprint()
    chat_id = get_config(module_name_honeypot='webhook', key='telegram', passwd=fingerprint, default='')
    if not chat_id:
        generate_qrcode(LOCAL_TOKEN)
        if search_chat_id_by_token(LOCAL_TOKEN, fingerprint):
            send_message_telegram("DeceptGold successfully configured telegram. Your notifications will be displayed here.", fingerprint)
    else:
        print("Telegram is already configured. If you want to configure notifications, first use '--telegram=false' to disable notifications and then enable them again.")


def reset_configuration_telegram():
    update_config('telegram', '', module_name='webhook')
