import os
import socket
import tempfile

from urllib.parse import urlparse


NAME_FILE_LOG = '.deceptgold.log'
NAME_FILE_PID = '.deceptgold.pid'

def parse_args(args):
    parsed = {}
    if args:
        if not args[0] is None:
            for arg in args:
                if '=' not in arg:
                    continue

                key, value = arg[:].split('=', 1)

                key = key.replace('-', '_').strip().lower()
                value = value.strip().lower()

                if value in ('true', '1', 'yes', 'on'):
                    parsed[key] = True
                elif value in ('false', '0', 'no', 'off'):
                    parsed[key] = False
                else:
                    parsed[key] = value

    return parsed

def my_self_developer():
    with open(__file__, 'r', encoding='utf-8') as my_self_dev:
        return '# Pyarmor' != my_self_dev.read(9).strip()

def get_temp_log_path(filename):
    return os.path.join(tempfile.gettempdir(), filename)


def check_open_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(2)
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ('http', 'https'), parsed.netloc])
    except Exception:
        return False
