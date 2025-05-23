import logging
import subprocess
import os
import signal
import sys

from cyclopts import App

from deceptgold.configuration.opecanary import generate_config
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.opencanary.help_opencanary import start_opencanary_internal
from deceptgold.helper.helper import parse_args, my_self_developer


logger = logging.getLogger(__name__)

services_app = App(name="service", help="Module service available")

import os
import tempfile

def get_temp_log_path(filename):
    return os.path.join(tempfile.gettempdir(), filename)

PID_FILE = get_temp_log_path("deceptgold.pid")
LOG_FILE = get_temp_log_path("deceptgold.log")


def pre_execution():
    logger.info("Performing pre-command operations.")
    generate_config()

def pre_execution_decorator(func):
    def wrapper(*args, **kwargs):
        pre_execution()
        if my_self_developer():
            return func(*args, **kwargs)
        else:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Error making encapsulated call. Check the documentation as the command is apparently being sent incorrectly. {e}")
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
    recall = parsed_args.get('recall', False)

    if my_self_developer():
        daemon = False

    p_force_no_wallet = 'force_no_wallet=True' if force_no_wallet else ''

    if get_config("user", "address", None) is None:
        if daemon and not force_no_wallet:
            print(f"The current user has not configured their public address to receive their rewards. The system will not continue. It is recommended to configure it before starting the fake services. Use the parameters: 'user --my-address 0xYourPublicAddress' or use the parameters 'service force-no-wallet=true' to continue without system interruption. But be careful, you will not be able to redeem your rewards now and/or retroactively.")
            sys.exit(1)

    msg_already_run = "The service is already running. Consider using the 'service stop' command to stop it from running if necessary."
    if not daemon:
        if not recall:
            if os.path.exists(PID_FILE):
                logger.warning(msg_already_run)
                print(msg_already_run)
                return None
        start_opencanary_internal(p_force_no_wallet)
    else:
        with open(LOG_FILE, 'a') as log:
            cmd = [sys.executable, "service", "start", "daemon=false", 'recall=true', p_force_no_wallet]
            process = subprocess.Popen(cmd, stdout=log, stderr=log)
            with open(PID_FILE, "w") as f:
                f.write(str(process.pid))


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
        logger.warning(f"Process {pid} finished executing.")
    except ProcessLookupError:
        logger.warning(f"Process {pid} not found.")
    except Exception as e:
        logger.warning(f"Error in stop deceptgold: {e}")
    finally:
        os.remove(PID_FILE)


@services_app.command(name="restart",
                      help="This functionality calls stop and then start. It will call start if stop succeeds "
                           "without errors. These calls call the respective default "
                            "attributes of each call.")
@pre_execution_decorator
def restart():
    try:
        stop()
        start()
    except Exception as e:
        logger.warning(f"Unable to restart the application. {e}")