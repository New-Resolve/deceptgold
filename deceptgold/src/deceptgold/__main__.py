import time
import timeit
import warnings
import logging
import multiprocessing

from cyclopts import App
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils.functional")
warnings.filterwarnings("ignore", category=SyntaxWarning)

from deceptgold.helper.descripton import get_description
from deceptgold.helper.opencanary.proxy_logger import CustomFileHandler

try:
    from deceptgold.commands.user import users_app
    from deceptgold.commands.service import services_app
    from deceptgold.commands.notify import notify_app
    from deceptgold.configuration import log
except ImportError as e:
    pass # print(e)

try:
    from deceptgold.src.deceptgold.commands.user import users_app
    from deceptgold.src.deceptgold.commands.service import services_app
    from deceptgold.src.deceptgold.commands.notify import notify_app
    from deceptgold.src.deceptgold.configuration.log import *
except ImportError as e:
    pass # print(e)

logger = logging.getLogger(__name__)
logging.FileHandler = CustomFileHandler

app = App(name="DeceptGold", help=get_description())
app.command(users_app)
app.command(services_app)
app.command(notify_app)


multiprocessing.set_start_method("spawn")


if __name__ == "__main__":
    if not hasattr(time, "clock"):
        time.clock = timeit.default_timer

    logger.info("Initialization complete the application.")
    app()
    logger.info("Finally application!")