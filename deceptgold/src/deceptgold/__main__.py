import time
import timeit
import warnings
import logging
import multiprocessing
import traceback
import importlib.metadata

from cyclopts import App
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils.functional")
warnings.filterwarnings("ignore", category=SyntaxWarning)


def _get_app_version() -> str:
    try:
        return importlib.metadata.version("deceptgold")
    except Exception:
        return "0.0.0"


def init_app():
    try:
        if not hasattr(time, "clock"):
            time.clock = timeit.default_timer

        from deceptgold.helper.descripton import get_description
        from deceptgold.helper.opencanary.proxy_logger import CustomFileHandler
        from deceptgold.helper.helper import my_self_developer
        from deceptgold.commands.user import users_app
        from deceptgold.commands.service import services_app
        from deceptgold.commands.notify import notify_app
        from deceptgold.configuration import log
        from deceptgold.helper.notify.telemetry.send import exec_telemetry


        logger = logging.getLogger(__name__)
        logging.FileHandler = CustomFileHandler
        logger.info("Initialization complete the application.")

        app = App(name="DeceptGold", help=get_description(), version=_get_app_version())

        exec_telemetry()

        app.command(users_app)
        app.command(services_app)
        app.command(notify_app)

        app()

        if logger:
            logger.info("Finally application!")

    except KeyboardInterrupt:
        pass
    except Exception:
        print(f"Critical error in the application. Please contact us to report this situation. We do not collect any "
              f"information. It would be necessary for you to send us specific information about this specific "
              f"situation. Help us to constantly improve. contact@decept.gold")
        if my_self_developer():
            traceback.print_exc()

    multiprocessing.set_start_method("spawn")



if __name__ == "__main__":
    init_app()