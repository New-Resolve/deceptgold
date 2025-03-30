import logging

from cyclopts import App, Parameter, Group
from typing import Annotated

try:
    from deceptgold.configuration.log import FILE_NAME_LOG_APP, setup_logging
except ImportError as e:
    logging.error(f"No module named 'deceptgold.configuration.log'. Original: {e}")

try:
    from deceptgold.src.deceptgold.configuration.log import FILE_NAME_LOG_APP, setup_logging
except ImportError as e:
    logging.error(f"No module named 'deceptgold.src.deceptgold.configuration.logg'. Original: {e}")

logger = logging.getLogger(__name__)

others_app = App(name="others", help="Others commands or configurations")


@others_app.command(name="--log-file", help="Added file destination logs.")
def config_log_file(filename: Annotated[str, Parameter(help="File name this log configuration")]):
    global FILE_NAME_LOG_APP
    logger.info("Actual logging file %s", FILE_NAME_LOG_APP)
    FILE_NAME_LOG_APP = filename
    setup_logging()
    logger.info("New logging file %s", filename)

