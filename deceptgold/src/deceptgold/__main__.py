import logging
import multiprocessing
import warnings

from cyclopts import App
from cryptography.utils import CryptographyDeprecationWarning

from deceptgold.help.descripton import get_description

try:
    from deceptgold.commands.user import users_app
    from deceptgold.commands.service import services_app
    from deceptgold.configuration import log
except ImportError as e:
    ...# print(e)

try:
    from deceptgold.src.deceptgold.commands.user import users_app
    from deceptgold.src.deceptgold.commands.service import services_app
    from deceptgold.src.deceptgold.configuration.log import *
except ImportError as e:
    ...# print(e)

logger = logging.getLogger(__name__)

app = App(name="DeceptGold", help=get_description())
app.command(users_app)
app.command(services_app)

warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
multiprocessing.set_start_method("spawn")


if __name__ == "__main__":
    logger.info("Initialization complete the application.")
    app()
    logger.info("Finally application!")