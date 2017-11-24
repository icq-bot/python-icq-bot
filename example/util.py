import logging
import os
import sys
from functools import wraps
from logging.handlers import RotatingFileHandler


class DynamicRotatingFileHandler(RotatingFileHandler):
    # noinspection PyPep8Naming
    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, delay=False):
        dir_name = os.path.dirname(filename)
        file_name = os.path.basename(filename)
        script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        filename = os.path.join(dir_name, script_name + file_name)

        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        super(DynamicRotatingFileHandler, self).__init__(
            filename=filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay
        )


def log_call(func):
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def _log(self, *args, **kwargs):
        logger.debug("Entering function: '{}'.".format(func.__qualname__))
        result = func(self, *args, **kwargs)
        logger.debug("Result is: '{}'.".format(result))
        logger.debug("Exiting function: '{}'.".format(func.__qualname__))
        return result

    return _log
