import os
import logging

def log_definition():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)  # Um nível acima
    log_dir = os.path.join(parent_dir, 'logs')  # Diretório 'logs' no nível acima

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, 'deceptgold.log')

logging.basicConfig(
    level=logging.INFO,
    filename=log_definition(),
    encoding="utf-8",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)