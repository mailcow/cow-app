import logging

LOGGER_NAME = "cow-app"
LOGGER_FORMAT = "[%(asctime)s] [%(ident)s] [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"

logger = logging.getLogger(LOGGER_NAME)
