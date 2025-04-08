import logging
import warnings
import multiprocessing

from cyclopts import App

from deceptgold.help.descripton import get_description

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

app = App(name="DeceptGold", help=get_description())

app.command(users_app)
app.command(services_app)



if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=ResourceWarning)
    multiprocessing.set_start_method("spawn")
    app()
    logger.info("Finally application!")