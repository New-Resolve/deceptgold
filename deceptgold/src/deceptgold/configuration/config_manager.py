import inspect
import os
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".deceptgold.conf"


def encode(data, passwd):
    return ''.join(chr(ord(c) ^ ord(passwd[i % len(passwd)])) for i, c in enumerate(data))

def decode(data, passwd):
    return encode(data, passwd)


def update_config(key: str, value: str, module_name=None, passwd=None):
    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    if not module_name:
        module_name = os.path.splitext(caller_filename)[0]

    config = {}
    if CONFIG_PATH.exists() and CONFIG_PATH.stat().st_size > 0:
        with open(CONFIG_PATH, "r") as file_config:
            config = json.load(file_config)

    if module_name not in config:
        config[module_name] = {}

    if passwd:
        value = encode(value, passwd)

    config[module_name][key] = value

    with open(CONFIG_PATH, "w") as file_config:
        json.dump(config, file_config, indent=4)

def get_config(module_name_honeypot: str, key: str, default=None, passwd=None):
    try:
        if CONFIG_PATH.exists() and CONFIG_PATH.stat().st_size > 0:
            with open(CONFIG_PATH, "r") as file_config_honeypot:
                config_honeypot = json.load(file_config_honeypot)
                result = config_honeypot[module_name_honeypot][key]
                if not passwd or result == default:
                    return result
                else:
                    return decode(config_honeypot.get(module_name_honeypot, {}).get(key, default), passwd)
        return default
    except KeyError:
        return default

