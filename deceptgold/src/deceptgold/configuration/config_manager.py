import inspect
import os
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".deceptgold.conf"

def update_config(key: str, value: str):
    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    module_name = os.path.splitext(caller_filename)[0]

    config = {}
    if CONFIG_PATH.exists() and CONFIG_PATH.stat().st_size > 0:
        with open(CONFIG_PATH, "r") as file_config:
            config = json.load(file_config)

    if module_name not in config:
        config[module_name] = {}
    config[module_name][key] = value

    with open(CONFIG_PATH, "w") as file_config:
        json.dump(config, file_config, indent=4)

def get_config(module_name_honeypot: str, key: str, default=None):
    if CONFIG_PATH.exists() and CONFIG_PATH.stat().st_size > 0:
        with open(CONFIG_PATH, "r") as file_config_honeypot:
            config_honeypot = json.load(file_config_honeypot)
            return config_honeypot.get(module_name_honeypot, {}).get(key, default)
    return default
