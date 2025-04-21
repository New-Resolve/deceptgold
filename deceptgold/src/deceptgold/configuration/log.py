import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename='deceptgold.log',
        encoding="utf-8",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

try:
    setup_logging()
except PermissionError as e:
    print("Permission failure occurred while executing the resource. Check if privileges are required or consider using Deceptgold with proper permissions.")
    sys.exit(13)
