import logging

from cyclopts import App

from deceptgold.helper.notify.telegram import configure_telegram, reset_configuration_telegram
from deceptgold.helper.notify.webhook import configure_webhook
from deceptgold.helper.helper import parse_args, is_valid_url


logger = logging.getLogger(__name__)

notify_app = App(name="notify", help="These are the configuration options regarding notifications to be sent to the honeypot administrator.")


@notify_app.command(name="--telegram=false", help="To disable sending notifications via telegram.")
def telegram():
    reset_configuration_telegram()


@notify_app.command(name="--telegram=true", help="Scan the QRCode or use a browser to read the URL. Synchronization will be automatic and you will be notified.")
def telegram():
    configure_telegram()


@notify_app.command(name="webhook", help="Sending requests to your return address. e.g. endpoint=\"https://example.com/webhook\":\n\n"
        "Warning:\n"
        "  To execute this command, you must provide the full address of your callback.\n\n"
        "Forwarding:\n"
        "  endpoint=\"https://example.com/webhook\"       Your complete webhook/callback address\n\n"        
        "Usage example:\n"
        "  deceptgold notify webhook endpoint=\"https://example.com/webhook\"")
def webhook(*args):
    """
    a
    """
    parsed_args = parse_args(args)
    webhook_endpoint = parsed_args.get('endpoint', '')
    if not is_valid_url(webhook_endpoint):
        notify_app.help_print()
        raise SystemExit(1)
    if webhook_endpoint:
        if not configure_webhook(webhook_endpoint):
            notify_app.help_print()
            raise SystemExit(1)

