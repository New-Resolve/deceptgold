import httpx

from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.fingerprint import get_machine_fingerprint


def send_message_webhook_discord(message_send, fingerprint=None):
    if not fingerprint:
        fingerprint = get_machine_fingerprint()
    endpoint_webhook_discord = get_config(module_name_honeypot='webhook', key='discord', passwd=fingerprint, default='')
    if endpoint_webhook_discord:
        httpx.post(url=endpoint_webhook_discord, json={"content": {"deceptgold": {"success": True, "msg": message_send}}})


def configure_webhook_discord(endpoint):
    if not endpoint:
        reset_configuration_discord()
        return True
    fingerprint = get_machine_fingerprint()
    try:
        r = httpx.post(url=endpoint, json={"content": {"deceptgold": {"success": True, "msg": "DeceptGold successfully configured discord webhook. Your notifications will be displayed here."}}})
        if r.status_code != 200:
            raise Exception("The callback discord address does not exist or is unreachable.")
        return update_config(module_name='webhook', key='discord', passwd=fingerprint, value=endpoint)
    except Exception as e:
        print(f"Failed to configure webhook. Verify that your discord webhook endpoint address is configured and working. {e}")
        return False


def reset_configuration_discord():
    update_config('discord', '', module_name='webhook')
