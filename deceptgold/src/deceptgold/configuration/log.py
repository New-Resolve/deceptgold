import os
import logging

FILE_NAME_LOG_APP = ""


def log_definition():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(os.path.dirname(base_dir), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, 'deceptgold.log')

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename=log_definition(),
        encoding="utf-8",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    global FILE_NAME_LOG_APP
    FILE_NAME_LOG_APP = log_definition()

setup_logging()