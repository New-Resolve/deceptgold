import logging
import subprocess

from cyclopts import App
from deceptgold.configuration.opecanary import generate_config

logger = logging.getLogger(__name__)

services_app = App(name="service", help="Module service available")

def pre_execution():
    logger.info("Executando operações prévias ao comando.")
    generate_config()

def pre_execution_decorator(func):
    def wrapper(*args, **kwargs):
        pre_execution()
        return func(*args, **kwargs)
    return wrapper

@services_app.command(name="--start", help="Start service(s) in operational system")
@pre_execution_decorator
def start():
    try:
        subprocess.run( ['opencanaryd', '--start'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error(e)


@services_app.command(name="--stop", help="Stop service(s) in operational system")
@pre_execution_decorator
def stop():
    try:
        subprocess.run(["opencanaryd", "--stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error(e)