import uuid
import requests
import time

import qrcode_terminal

from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.fingerprint import get_machine_fingerprint

BOT_TOKEN = "7817219543:AAG3inIRElxo8VHVcncYTJw8DJOIjlz9018"
LOCAL_TOKEN = str(uuid.uuid4())[-17:]

def generate_qrcode(token=LOCAL_TOKEN):
    url = f"https://t.me/DeceptGoldBot?start={token}"
    qrcode_terminal.draw(url)
    print(f"Scan the QRCode above to open in Telegram: {url} ⏳ Waiting for binding...")

def search_chat_id_by_token(token_local, fingerprint):
    offset = None
    try:
        while True:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params={"offset": offset})
            updates = r.json()["result"]
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                txt = msg.get("text", "")
                if txt.startswith("/start ") and txt.split(" ")[1] == token_local:
                    chat_id = msg["chat"]["id"]
                    update_config('chat_id', str(chat_id), module_name='telegram', passwd=fingerprint)
                    print("Telegram notifications have been successfully configured.")
                    return True
            time.sleep(2)
    except KeyboardInterrupt:
        print("Process interrupted by user. Telegram notifications have not been configured.")
        return False
    except Exception as e:
        print(f"Error: {e}")

def send_message_telegram(test_message, fingerprint=None):
    if not fingerprint:
        fingerprint = get_machine_fingerprint()
    chat_id = get_config(module_name_honeypot='telegram', key='chat_id', passwd=fingerprint, default='')
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": int(chat_id),
        "text": test_message
    }
    r = requests.post(url, data=payload)
    if not r.ok:
        print("Error sending notification to telegram.")


def configure_telegram():
    fingerprint = get_machine_fingerprint()
    chat_id = get_config(module_name_honeypot='telegram', key='chat_id', passwd=fingerprint, default='')
    if not chat_id:
        generate_qrcode(LOCAL_TOKEN)
        if search_chat_id_by_token(LOCAL_TOKEN, fingerprint):
            send_message_telegram("DeceptGold successfully configured. Your notifications will be displayed here.", fingerprint)
    else:
        print("Telegram is already configured. If you want to configure notifications, first use '--telegram=false' to disable notifications and then enable them again.")


def reset_configuration_telegram():
    update_config('chat_id', '', module_name='telegram')
