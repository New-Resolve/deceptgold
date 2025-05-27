import inspect
import logging
import os
import json
from pathlib import Path

logging = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".deceptgold.conf"


def encode(data, passwd):
    return ''.join(chr(ord(c) ^ ord(passwd[i % len(passwd)])) for i, c in enumerate(data))

def decode(data, passwd):
    return encode(data, passwd)


def update_config(key: str, value: str, module_name=None, passwd=None, config_file=None):
    if not config_file:
        config_file = CONFIG_PATH
    config_file = Path(config_file)
    caller_frame = inspect.stack()[1]
    caller_filename = os.path.basename(caller_frame.filename)
    if not module_name:
        module_name = os.path.splitext(caller_filename)[0]

    config = {}
    if config_file.exists() and config_file.stat().st_size > 0:
        with open(config_file, "r") as file_config:
            config = json.load(file_config)

    if module_name not in config:
        config[module_name] = {}

    if passwd:
        value = encode(value, passwd)

    config[module_name][key] = value

    with open(config_file, "w") as file_config:
        json.dump(config, file_config, indent=4)

def get_config(module_name_honeypot: str, key: str, default=None, passwd=None, file_config=None):
    if not file_config:
        file_config = CONFIG_PATH
    file_config = Path(file_config)
    try:
        if file_config.exists() and file_config.stat().st_size > 0:
            with open(file_config, "r") as file_config_honeypot:
                config_honeypot = json.load(file_config_honeypot)
                result = config_honeypot[module_name_honeypot][key]
                if not passwd or result == default:
                    return result
                else:
                    return decode(config_honeypot.get(module_name_honeypot, {}).get(key, default), passwd)
        return default
    except KeyError:
        return default
    except:
        logging.error('Error searching for previously tokenized requisitions. The contagem of requisitions will be accounted for from the first moment of the configuration file.')
        return  default

