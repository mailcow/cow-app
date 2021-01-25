import logging

LOGGER_NAME = 'cow-app'
LOGGER_FORMAT = '%(process)d %(asctime)s-%(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S %z'

logging.basicConfig(format=LOGGER_FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger(LOGGER_NAME)
