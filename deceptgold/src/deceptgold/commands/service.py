import subprocess
import os
import psutil
import sys
import logging
import platform
import json

from pathlib import Path
from cyclopts import App, Group, Parameter
from typing import Annotated

from deceptgold.configuration.opecanary import generate_config, toggle_config, PATH_CONFIG_OPENCANARY
from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.opencanary.help_opencanary import start_opencanary_internal
from deceptgold.helper.helper import parse_args, my_self_developer, get_temp_log_path, check_open_port
from deceptgold.helper.helper import NAME_FILE_LOG, NAME_FILE_PID
from deceptgold.helper.notify.notify import check_send_notify


hidden_group = Group(name="Hidden group", show=False)

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
        if parse_args(args).get('debug', False):
            return func(*args, **kwargs)
        else:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Error making encapsulated call. Check the documentation as the command is apparently being sent incorrectly.")
    return wrapper

# @profile
@services_app.command(name="start", help=(
        "Start service(s) in operational system.\n\n"
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
        try:
            if not recall:
                if os.path.exists(PID_FILE):
                    print(msg_already_run)
                    return None
            start_opencanary_internal(p_force_no_wallet, debug)
        finally:
            check_send_notify("Deceptgold has been finalized.")
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


@services_app.command(name="stop", help="Stop service(s) in operational system.")
@pre_execution_decorator
def stop():
    if not os.path.exists(PID_FILE):
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=5)
            pass
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logging.warning(f"Error stopping process: {e}")
    except ProcessLookupError:
        pass
    except Exception as e:
        logging.warning(f"Error in stop deceptgold: {e}")
    finally:
        os.remove(PID_FILE)


@services_app.command(name="restart",
                      help="This functionality calls stop and then start. It will call start if stop succeeds without errors.")
@pre_execution_decorator
def restart():
    try:
        stop()
        start()
    except Exception as e:
        logger.warning(f"Unable to restart the application. {e}")


@services_app.command(name="exec", group=hidden_group)
def exec_python(*code_python: str):
    """
    Execute Python code inside the packaged environment.
    Example: deceptgold service exec 'import passlib; print(passlib.__version__)'
    """
    try:
        exec(" ".join(code_python))
    except Exception as e:
        print(f"[ERROR] {e}")


@services_app.command(name="enable")
def enable_service(service_name: str):
    """
    Enables a service in the Deceptgold.
    Example: enable ssh
    """
    toggle_config(service_name, 'enabled', True)

@services_app.command(name="disable")
def disable_service(service_name: str):
    """
    Disable a service in the Deceptgold.
    Example: disable ssh
    """
    toggle_config(service_name, 'enabled', False)

@services_app.command(name="set")
def set_port(service_name: str, new_port: int):
    """
    Update the port of the specific deceptgold service
    Example: set ssh 2223
    """
    try:
        toggle_config(service_name, 'port', new_port)
    except Exception as e:
        print(f"Unable to set port '{service_name}' to '{new_port}'. {e}")

@services_app.command(name="status")
def status():
    """
    Capture the services that are enabled and check the status of each specific port whether it is open or closed.
    """
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as pid:
            print(f"The Process started through the PID: {pid.read()}")

    with open(PATH_CONFIG_OPENCANARY) as conf:
        data = json.load(conf)

    enabled_services = []

    for key, value in data.items():
        if key.endswith('.enabled') and value is True:
            service = key.split('.')[0]
            port_key = f"{service}.port"
            port = data.get(port_key, "N/A")
            enabled_services.append((service.upper(), port))

    print("Enabled services and their respective ports:")
    print(f"{'Service':<15} {'Port':<6} {'Status':<6}")
    print("-" * 30)
    for service, port in enabled_services:
        status_service = "OPEN" if check_open_port("127.0.0.1", port) else "CLOSED"
        print(f"{service:<15} {port:<6} {status_service:<6}")



@services_app.command(name="list")
def list_services():
    """
    Command to list all configured services showing the status of each service independent of activation.
    """
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as pid:
            print(f"The Process started through the PID: {pid.read()}")

    with open(PATH_CONFIG_OPENCANARY) as conf:
        data = json.load(conf)

    enabled_services = []

    for key, value in data.items():
        service = key.split('.')[0]
        port_key = f"{service}.port"
        port = data.get(port_key, "N/A")
        enabled_services.append((service.upper(), port))

    enabled_services = list(dict.fromkeys(enabled_services))

    print("Below are all the services available and capable of being configured.")
    print(f"{'Service':<15} {'Port':<6} {'Status':<6}")
    print("-" * 30)
    for service, port in enabled_services:
        if str(port).lower().strip() == 'n/a' or 'banner' in service.lower().strip():
            continue

        status_service = "OPEN" if check_open_port("127.0.0.1", port) else "CLOSED"
        print(f"{service:<15} {port:<6} {status_service:<6}")



@services_app.command(name="--node_id", help="Provide the desired name for recognition of this machine for the entire deceptgold system.")
def register(node_id: Annotated[str, Parameter(help="The default recognized name is the hostname configured in your system's environment variables.")]):
    # Reuse of the configuration function. It is due to the reuse of code that the service name is device.
    toggle_config('device', 'node_id', node_id)





