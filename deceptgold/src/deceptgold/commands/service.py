import logging
import subprocess
import os
import signal
import sys


from cyclopts import App, Parameter
from typing import Annotated
from deceptgold.configuration.opecanary import generate_config
from deceptgold.help.opencanary.help_opencanary import start_opencanary_internal

logger = logging.getLogger(__name__)

services_app = App(name="service", help="Module service available")

PID_FILE = "/tmp/deceptgold.pid"
LOG_FILE = "/tmp/deceptgold.log"


def pre_execution():
    logger.info("Executando operações prévias ao comando.")
    generate_config()

def pre_execution_decorator(func):
    def wrapper(*args, **kwargs):
        pre_execution()
        return func(*args, **kwargs)
    return wrapper


@services_app.command(name="start", help="Start service(s) in operational system")
@pre_execution_decorator
def start(
):
    if os.path.exists(PID_FILE):
        logger.warning("Service is already running.")
        return
    start_opencanary_internal()

    # if not daemon:
    #     if os.path.exists(PID_FILE):
    #         logger.warning("Service is already running.")
    #         return
    #     start_opencanary_internal()
    # else:
    #     if os.path.exists(PID_FILE):
    #         logger.warning("Service is already running.")
    #         return
    #     python_exec = sys.executable
    #     with open(LOG_FILE, "w") as out:
    #         process = subprocess.Popen(
    #             [python_exec, "-m", "deceptgold.entrypoints.opencanary_runner"],
    #             stdout=out,
    #             stderr=out,
    #             start_new_session=True,
    #         )
    #     with open(PID_FILE, "w") as f:
    #         f.write(str(process.pid))
    #     logger.info(f"Service started in background with PID {process.pid}. File: {LOG_FILE}")

@services_app.command(name="stop", help="Stop service(s) in operational system")
@pre_execution_decorator
def stop():
    if not os.path.exists(PID_FILE):
        logger.warning("Service is not running.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Process {pid} finished executing.")
    except ProcessLookupError:
        logger.warning(f"Process {pid} not found.")
    finally:
        os.remove(PID_FILE)