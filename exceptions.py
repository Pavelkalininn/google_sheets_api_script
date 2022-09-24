import logging


class UpdateException(Exception):
    def __init__(self, message):
        logging.error(message)


class CriticalException(Exception):
    def __init__(self, message):
        logging.critical(message)
