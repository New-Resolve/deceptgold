import httpx

from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.fingerprint import get_machine_fingerprint


def send_message_webhook_slack(message_send, fingerprint=None):
    if not fingerprint:
        fingerprint = get_machine_fingerprint()
    endpoint_webhook_slack = get_config(module_name_honeypot='webhook', key='slack', passwd=fingerprint, default='')
    if endpoint_webhook_slack:
        httpx.post(url=endpoint_webhook_slack, json={"text": {"deceptgold": {"success": True, "msg": message_send}}})


def configure_webhook_slack(endpoint):
    if not endpoint:
        reset_configuration_slack()
        return True
    fingerprint = get_machine_fingerprint()
    try:
        r = httpx.post(url=endpoint, json={"text": {"deceptgold": {"success": True, "msg": "DeceptGold successfully configured slack webhook. Your notifications will be displayed here."}}})
        if r.status_code != 200:
            raise Exception("The callback slack address does not exist or is unreachable.")
        return update_config(module_name='webhook', key='slack', passwd=fingerprint, value=endpoint)
    except Exception as e:
        print(f"Failed to configure webhook. Verify that your slack webhook endpoint address is configured and working. {e}")
        return False


def reset_configuration_slack():
    update_config('slack', '', module_name='webhook')
