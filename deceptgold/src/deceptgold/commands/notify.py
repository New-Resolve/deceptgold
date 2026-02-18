import logging

from cyclopts import App

from deceptgold.helper.notify.telegram import configure_telegram, reset_configuration_telegram
from deceptgold.helper.notify.webhook import configure_custom_webhook
from deceptgold.helper.notify.slack import configure_webhook_slack
from deceptgold.helper.notify.discord import configure_webhook_discord
from deceptgold.helper.helper import parse_args, is_valid_url
from deceptgold.configuration.config_manager import get_config, update_config
from deceptgold.helper.message_formatter import MessageTemplates


logger = logging.getLogger(__name__)

notify_app = App(name="notify", help="These are the configuration options regarding notifications to be sent to the honeypot administrator.")


@notify_app.command(name="--telegram=false", help="To disable sending notifications via telegram.")
def telegram():
    reset_configuration_telegram()


@notify_app.command(name="--telegram=true", help="Scan the QRCode or use a browser to read the URL. Synchronization will be automatic and you will be notified.")
def telegram():
    configure_telegram()


@notify_app.command(name="--mode=default", help="Use default notifications (system events only).")
def mode_default():
    update_config('notify_mode', 'default', module_name='webhook')
    print(MessageTemplates.notify_default_mode())


@notify_app.command(name="--mode=ai", help="Use AI-generated notifications (requires LLM model downloaded).")
def mode_ai():
    if not _check_ai_model_available():
        print(MessageTemplates.notify_ai_mode_intelligence_required())
        return
    
    update_config('notify_mode', 'ai', module_name='webhook')
    print(MessageTemplates.notify_ai_mode_activated())


def _check_ai_model_available():
    try:
        from deceptgold.helper.ai_model import check_ai_model_available_silent
        return check_ai_model_available_silent()
    except Exception:
        return False


@notify_app.command(name="webhook", help="Sending requests to your return address. e.g. custom=\"https://example.com/webhook\".\n\n"
        "Warning:\n"
        "  To execute this command, you must provide the full address of your callback.\n\n"
        "For your own custom address:\n"                              
        "  custom=\"https://example.com/webhook\"                       Your custom complete string address\n\n"        
        "To use the slack bot address:\n"
        "  slack=\"https://hooks.slack.com/services/G1Z/BQA/71cKYc\"    Your slack complete string address\n\n"                                           
        "To use the jira system address:\n"
        "  jira=\"https://api.yoursite.com/jira/webhook\"               Your jira complete string address\n\n"
        "To use the discord messages address:\n"
        "  discord=\"https://discord.com/api/webhooks/1238/abRSTUVWX\"  Your discord complete string address\n\n"                                                    
        "Usage example:\n"
        "  deceptgold notify webhook custom=\"https://example.com/webhook\"")
def webhook(*args):
    if not args:
        notify_app.help_print()
        raise SystemExit(1)
    parsed_args = parse_args(args)
    webhook_endpoint = parsed_args.get('custom', '')
    if webhook_endpoint:
        if not is_valid_url(webhook_endpoint):
            notify_app.help_print()
            raise SystemExit(1)
        if webhook_endpoint:
            if not configure_custom_webhook(webhook_endpoint):
                notify_app.help_print()
                raise SystemExit(1)

    slack_endpoint = parsed_args.get('slack', '')
    if slack_endpoint:
        if not is_valid_url(slack_endpoint):
            notify_app.help_print()
            raise SystemExit(1)
        if slack_endpoint:
            if not configure_webhook_slack(slack_endpoint):
                notify_app.help_print()
                raise SystemExit(1)

    discord_endpoint = parsed_args.get('discord', '')
    if discord_endpoint:
        if not is_valid_url(discord_endpoint):
            notify_app.help_print()
            raise SystemExit(1)
        if discord_endpoint:
            if not configure_webhook_discord(discord_endpoint):
                notify_app.help_print()
                raise SystemExit(1)