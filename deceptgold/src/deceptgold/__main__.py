import logging

from cyclopts import App

try:
    from deceptgold.commands.user import users_app
    from deceptgold.commands.others import others_app
    from deceptgold.configuration import log
except ImportError as e:
    logging.error(f"Erro in import module(s). Original:{e}")

try:
    from deceptgold.src.deceptgold.commands.user import users_app
    from deceptgold.src.deceptgold.commands.others import others_app
    from deceptgold.src.deceptgold.configuration.log import *
except ImportError as e:
    logging.error(f"Erro in import module(s). Original: {e}")

logger = logging.getLogger(__name__)
logger.info("Iniciando aplicação deceptgold")

app = App(name="DeceptGold", help="DDP category CLI application for cyber attack monitoring.")

app.command(users_app)
app.command(others_app)


if __name__ == "__main__":
    app()
    logger.info("Saida da aplicação!")