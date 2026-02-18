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
    my_self_developer_fn = None
    try:
        if not hasattr(time, "clock"):
            time.clock = timeit.default_timer

        from deceptgold.helper.descripton import get_description
        from deceptgold.helper.opencanary.proxy_logger import CustomFileHandler
        from deceptgold.helper.helper import my_self_developer as my_self_developer_fn
        from deceptgold.helper.message_formatter import MessageFormatter, MessageTemplates
        from deceptgold.commands.user import users_app
        from deceptgold.commands.service import services_app
        from deceptgold.commands.notify import notify_app
        from deceptgold.commands.ai import ai_app
        from deceptgold.commands.reports import reports_app
        from deceptgold.configuration import log
        from deceptgold.helper.notify.telemetry.send import exec_telemetry
        from deceptgold.helper.ai_model import ensure_default_model_installed, list_installed_models


        logger = logging.getLogger(__name__)
        logging.FileHandler = CustomFileHandler
        logger.info("Initialization complete the application.")

        app = App(name="DeceptGold", help=get_description(), version=_get_app_version())

        # Check if AI models are installed, if not show installation interface
        installed_models = list_installed_models()
        if not installed_models:
            # Import and run the AI model installation command
            from deceptgold.commands.ai import install_model
            try:
                install_model()
            except SystemExit:
                pass  # User may have cancelled installation
        else:
            ensure_default_model_installed(interactive=True)

        exec_telemetry()

        app.command(users_app)
        app.command(services_app)
        app.command(notify_app)
        app.command(ai_app)
        app.command(reports_app)

        app()

        if logger:
            logger.info("Finally application!")

    except KeyboardInterrupt:
        pass
    except Exception:
        print(f"Critical error in the application. Please contact us to report this situation. We do not collect any "
              f"information. It would be necessary for you to send us specific information about this specific "
              f"situation. Help us to constantly improve. https://decept.gold")
        import os
        if callable(my_self_developer_fn) and my_self_developer_fn():
            traceback.print_exc()
        elif os.environ.get('DECEPTGOLD_DEBUG') == '1':
            traceback.print_exc()

    multiprocessing.set_start_method("spawn")



if __name__ == "__main__":
    init_app()