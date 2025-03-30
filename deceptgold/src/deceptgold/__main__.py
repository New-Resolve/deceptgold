import logging

from cyclopts import App


try:
    from deceptgold.commands.user import users_app
    from deceptgold.configuration import log
except ImportError:
    ...

try:
    from deceptgold.src.deceptgold.commands.user import users_app
    from deceptgold.src.deceptgold.configuration.log import *
except ImportError:
    ...

logger = logging.getLogger(__name__)
logger.info("Iniciando aplicação deceptgold")

app = App(name="DeceptGold", help="DDP category CLI application for cyber attack monitoring.")

app.command(users_app)


if __name__ == "__main__":
    app()
    logger.info("Saida da aplicação!")