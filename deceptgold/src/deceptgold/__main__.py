import logging

from cyclopts import App

try:
    from deceptgold.commands.user import users_app
    from deceptgold.commands.service import services_app
    from deceptgold.configuration import log
except ImportError as e:
    ...

try:
    from deceptgold.src.deceptgold.commands.user import users_app
    from deceptgold.src.deceptgold.commands.service import services_app
    from deceptgold.src.deceptgold.configuration.log import *
except ImportError as e:
    ...

logger = logging.getLogger(__name__)
logger.info("Initialization complete the application.")

app = App(name="DeceptGold", help="DDP category CLI application for cyber attack monitoring.")

app.command(users_app)
app.command(services_app)



if __name__ == "__main__":
    app()
    logger.info("Finally application!")