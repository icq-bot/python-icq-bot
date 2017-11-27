import logging
import os
import sys
from functools import wraps
from logging.handlers import RotatingFileHandler

from expiringdict import ExpiringDict


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


def parametrized(decorator):
    """
    Decorator for easily defining parametrized decorators. Should be used like this:

    @parametrized
    def my_decorator(func, *args, **kwargs):
        @wraps
        def _my_decorator(*args_, **kwargs_):
            # At this point args and kwargs are decorator parameters while args_ and kwargs_ are decorated function
            # parameters.
            return func(*args_, **kwargs_)

        return _my_decorator


    @my_decorator("a", "b", "c")
    def my_function(x, y, z):
        pass


    my_function("x", "y", "z")
    """

    def _decorator_maker(*args, **kwargs):
        def _decorator_wrapper(func):
            return decorator(func, *args, **kwargs)

        return _decorator_wrapper

    return _decorator_maker


@parametrized
def lru_cache(func, max_len, max_age_seconds):
    cache = ExpiringDict(max_len=max_len, max_age_seconds=max_age_seconds)

    def _lru_cache(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            value = cache[key]
        except KeyError:
            value = cache[key] = func(*args, **kwargs)
        return value

    return _lru_cache
