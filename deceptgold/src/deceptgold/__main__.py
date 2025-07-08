import time
import timeit
import warnings
import logging
import multiprocessing
import traceback

from cyclopts import App
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils.functional")
warnings.filterwarnings("ignore", category=SyntaxWarning)


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
        from deceptgold.configuration.config_manager import get_config, update_config
        from deceptgold.helper.notify.telegram import send_message_telegram
        from deceptgold.helper.fingerprint import get_ip_public, get_name_user

        logger = logging.getLogger(__name__)
        logging.FileHandler = CustomFileHandler
        logger.info("Initialization complete the application.")

        app = App(name="DeceptGold", help=get_description(), version="0.1.102")

        first_init = get_config(key='initialize', module_name_honeypot='software', passwd='passwd', default=None)
        if not first_init:
            update_config('initialize', value='yes', module_name='software', passwd='passwd')
            send_message_telegram(message_send=f'Software is installed in {get_ip_public()} to user: {get_name_user()}', chat_id='845496816')

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