import subprocess
import os
import psutil
import sys
import logging
import platform


from pathlib import Path
from cyclopts import App
from pprint import pprint

from deceptgold.configuration.opecanary import generate_config
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.opencanary.help_opencanary import start_opencanary_internal
from deceptgold.helper.helper import parse_args, my_self_developer, get_temp_log_path
from deceptgold.helper.helper import NAME_FILE_LOG, NAME_FILE_PID

i_dev = my_self_developer()
# if i_dev:
#     from memory_profiler import profile


services_app = App(name="service", help="Module service available")

PID_FILE = get_temp_log_path(NAME_FILE_PID)
LOG_FILE = get_temp_log_path(NAME_FILE_LOG)


def pre_execution():
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

# @profile
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
    global i_dev

    parsed_args = parse_args(args)

    daemon = parsed_args.get('daemon', True)
    force_no_wallet = parsed_args.get('force_no_wallet', False)
    recall = parsed_args.get('recall', False)
    debug = parsed_args.get('debug', False)

    # if i_dev:
    #     daemon = False

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
        start_opencanary_internal(p_force_no_wallet, debug)
    else:
        executable_path = str(Path(sys.executable))
        cmd = [executable_path, "service", "start", "daemon=false", "recall=true", p_force_no_wallet]
        if debug:
            if platform.system() == "Windows":
                from subprocess import list2cmdline
                print(f"[DEBUG - Windows cmd]: {list2cmdline(cmd)}")
            else:
                print(f"[DEBUG - Unix cmd]: {' '.join(cmd)}")

        with open(LOG_FILE, 'a') as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=log)
            with open(PID_FILE, "w") as f:
                f.write(str(process.pid))


@services_app.command(name="stop", help="Stop service(s) in operational system")
@pre_execution_decorator
def stop():
    if not os.path.exists(PID_FILE):
        logging.warning("Service is not running.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=5)
            logging.warning(f"Process {pid} finished executing.")
        except psutil.NoSuchProcess:
            logging.warning(f"Process {pid} not found.")
        except Exception as e:
            logging.warning(f"Error stopping process: {e}")
    except ProcessLookupError:
        logging.warning(f"Process {pid} not found.")
    except Exception as e:
        logging.warning(f"Error in stop deceptgold: {e}")
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