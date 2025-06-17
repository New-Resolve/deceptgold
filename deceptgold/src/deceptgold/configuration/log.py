# import logging
# import sys

# from deceptgold.configuration.opecanary import filelog_temp

# def setup_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         # filename=filelog_temp,
#         encoding="utf-8",
#         filemode="a",
#         format="%(asctime)s - %(levelname)s - %(message)s",
#         datefmt="%Y-%m-%d %H:%M:%S"
#     )

# try:
#     setup_logging()
# except PermissionError as e:
#     print("Permission failure occurred while executing the resource. Check if privileges are required or consider using Deceptgold with proper permissions.")
#     sys.exit(13)
