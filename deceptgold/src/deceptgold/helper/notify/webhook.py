import httpx

from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.fingerprint import get_machine_fingerprint


def send_message_custom_webhook(message_send, fingerprint=None):
    if not fingerprint:
        fingerprint = get_machine_fingerprint()
    endpoint_webhook = get_config(module_name_honeypot='webhook', key='custom', passwd=fingerprint, default='')
    if endpoint_webhook:
        httpx.post(url=endpoint_webhook, json={"deceptgold": {"success": True, "msg": message_send}})


def configure_custom_webhook(endpoint):
    if not endpoint:
        reset_configuration_custom_webhook()
        return True
    fingerprint = get_machine_fingerprint()
    try:
        r = httpx.post(url=endpoint, json={"deceptgold": {"success": True, "msg": "DeceptGold successfully configured custom webhook. Your notifications will be displayed here."}})
        if r.status_code != 200:
            raise Exception("The callback address does not exist or is unreachable.")
        return update_config(module_name='webhook', key='custom', passwd=fingerprint, value=endpoint)
    except Exception as e:
        print(f"Failed to configure webhook. Verify that your custom webhook endpoint address is configured and working. {e}")
        return False


def reset_configuration_custom_webhook():
    update_config('custom', '', module_name='webhook')
