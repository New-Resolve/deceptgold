import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename='deceptgold.log',
        encoding="utf-8",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

setup_logging()