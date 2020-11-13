"""
This contains methods for logging for GeoCube

Credits: Adopted from quest python library
"""
import logging
import os

import appdirs

_LOGGER = logging.getLogger("geocube")
_LOGGER.addHandler(logging.NullHandler())
_LOGGER.propagate = False
_LOGGER_FORMAT_STR = "%(levelname)s-%(name)s: %(message)s"


def get_logger():
    """
    Retrieve the logger for GeoCube

    Returns
    -------
    :class:`logging.Logger`
    """
    return _LOGGER


def set_log_level(level=None):
    """
    Sets the log level of the logger.

    Parameters
    ----------
    level: string, optional, default=None
        Level of logging; whichever level is chosen all higher levels
        will be logged. See: https://docs.python.org/2/library/logging.html#levels
    """
    if level is not None:
        _LOGGER.setLevel(level)
    else:
        _LOGGER.setLevel(logging.WARNING)


def _remove_log_handler(handler_type):
    for handle in _LOGGER.handlers:
        if isinstance(handle, handler_type):
            _LOGGER.removeHandler(handle)


def log_to_console(status=True, level=None):
    """Log events to the console.

    Parameters
    ----------
    status: bool, optional, default=True
        Whether logging to console should be turned on(True) or off(False)
    level: string, optional, default=None
        Level of logging; whichever level is chosen all higher levels
        will be logged. See: https://docs.python.org/2/library/logging.html#levels

    """
    set_log_level(level)
    if status:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(_LOGGER_FORMAT_STR)
        console_handler.setFormatter(formatter)
        _LOGGER.addHandler(console_handler)
    else:
        _remove_log_handler(logging.StreamHandler)


def log_to_file(status=True, filename=None, level=None):
    """Log events to a file.

    Parameters
    ----------
    status: bool, optional, default=True
        Whether logging to console should be turned on(True) or off(False)
    filename: string, optional, default=None
        path of file to log to
    level: string, optional, default=None
        Level of logging; whichever level is chosen all higher levels
        will be logged. See: https://docs.python.org/2/library/logging.html#levels

    """
    set_log_level(level)

    if filename is None:
        filename = os.path.join(appdirs.user_log_dir("geocube", "logs"), "geocube.log")

    if status:
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError:
            pass

        file_handler = logging.FileHandler(filename)
        formatter = logging.Formatter(_LOGGER_FORMAT_STR)
        file_handler.setFormatter(formatter)
        _LOGGER.addHandler(file_handler)
    else:
        _remove_log_handler(logging.FileHandler)
