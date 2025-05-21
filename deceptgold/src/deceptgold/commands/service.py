import logging
import subprocess
import os
import signal
import sys

from cyclopts import App
from deceptgold.configuration.opecanary import generate_config
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.opencanary.help_opencanary import start_opencanary_internal
from deceptgold.helper.helper import parse_args


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
        try:
            return func(*args, **kwargs)
        except Exception:
            print("Error making encapsulated call. Check the documentation as the command is apparently being sent incorrectly.")
    return wrapper

@services_app.command(name="start", help=(
        "Start service(s) in operational system\n\n"
        "Warning:\n"
        "  To execute this command you must inform your public wallet address to receive your rewards.\n\n"
        "Verbosity:\n"
        "  daemon=true|false              Run in background (default: true)\n\n"
        "Forced arguments:\n"
        "  force-no-wallet=true|false     Skip wallet verification (default: false)\n\n"
        "Usage example:\n"
        "  deceptgold service start daemon=false force-no-wallet=true"
    ))
@pre_execution_decorator
def start(*args):
    parsed_args = parse_args(args)

    daemon = parsed_args.get('daemon', True)
    force_no_wallet = parsed_args.get('force_no_wallet', False)

    p_force_no_wallet = ''
    if force_no_wallet:
        p_force_no_wallet = 'force_no_wallet=True'

    if get_config("user", "address", None) is None:
        if daemon and not force_no_wallet:
            print(f"The current user has not configured their public address to receive their rewards. The system no will continue. It is recommended to configure it before starting the fake services. Use the force-no-wallet=true parameter to continue without system interruption. But be careful, you will not be able to redeem your rewards now and retroactively.")
            sys.exit(1)

    msg_already_run = "The service is already running. Consider using the 'stop' command to stop it from running if necessary."
    if not daemon:
        if os.path.exists(PID_FILE):
            logger.warning(msg_already_run)
            print(msg_already_run)
            return None
        start_opencanary_internal(p_force_no_wallet)
    else:
        if os.path.exists(PID_FILE):
            logger.warning(msg_already_run)
            print(msg_already_run)
            return None

        python_exec = sys.executable
        with open(LOG_FILE, "w") as out:
            process = subprocess.Popen(
                [python_exec, "-m", "deceptgold.entrypoints.opencanary_runner", p_force_no_wallet],
                stdout=out,
                stderr=out,
                start_new_session=True,
            )
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
        logger.info(f"Service started in background with PID {process.pid}. File: {LOG_FILE}")

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
    except Exception as e:
        logger.warning("Error in stop deceptgold: {e}")
    finally:
        os.remove(PID_FILE)