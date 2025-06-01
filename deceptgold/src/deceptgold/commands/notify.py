import logging

from cyclopts import App

from deceptgold.helper.notify.telegram import configure_telegram, reset_configuration_telegram


logger = logging.getLogger(__name__)

notify_app = App(name="notify", help="These are the configuration options regarding notifications to be sent to the honeypot administrator.")


@notify_app.command(name="--telegram=false", help="To disable sending notifications via telegram.")
def telegram():
    reset_configuration_telegram()


@notify_app.command(name="--telegram=true", help="Scan the QRCode or use a browser to read the URL. Synchronization will be automatic and you will be notified.")
def telegram():
    configure_telegram()