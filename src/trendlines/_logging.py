# -*- coding: utf-8 -*-
"""
"""
import logging
import time
import zlib
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_FMT = (
    "%(asctime)s.%(msecs)03dZ"
    "|%(levelname)-8.8s"
    "|%(module)-18.18s"
    "|%(lineno)4d"
    "|%(funcName)-16.16s"
    "|%(message)s"
)
DATE_FMT = "%Y-%m-%dT%H-%M-%S"


class CustomFormatter(logging.Formatter):
    # Record times in UTC. Because that's the smart thing to do.
    converter = time.gmtime

    def format(self, record):
        return super(CustomFormatter, self).format(record)


def setup_logging(to_console=True, to_file=False, log_path=None):
    """
    Setup logging for this project.

    Parameters
    ----------
    to_console : bool, optional
        If ``True``, enable logging to the console.
    to_file : bool, optional
        If ``True``, enable logging to a file.
    log_path : str, optional
        The file to log to, if ``to_file`` is ``True``.

    Returns
    -------
    logger : :class:`logging.Logger`
        The created logger instance.
    """
    logger = logging.getLogger("trendlines")
    logger.setLevel(logging.DEBUG)

    if to_console:
        _setup_console_logging(logger)
    if to_file:
        _setup_file_logging(logger, Path(log_path))

    return logger


# Custom namer and rotator
# Taken from https://docs.python.org/3/howto/logging-cookbook.html
def _gzip_namer(name):
    return name + ".gz"


def _gzip_rotator(source, dest):
    """
    Compress the source file into the dest.

    Keeps the most recent rotation uncompressed.

    Parameters
    ----------
    source : :class:`pathlib.Path`
    dest : :class:`pathlib.Path`
    """
    with open(str(source), 'rb') as open_source:
        data = open_source.read()
        compressed = zlib.compress(data)
        with open(str(dest), 'wb') as open_dest:
            open_dest.write(compressed)

    # Keep a copy of the most recent rotation uncompressed to make things
    # easier for users.
    source.replace(dest + ".1")

    source.unlink()


def _setup_file_logging(logger, log_path):
    """
    Parameters
    ----------
    logger :
        The logger to modify
    log_path : :class:`pathlib.Path`
        The file and path to log to.
    """
    name = "File Handler"

    # Make our log dir and file.
    log_path.mkdir(mode=0x0755, parents=True, exist_ok=True)
    log_path.chmod(0x0664)

    # Create the handler and have it compress old files.
    handler = RotatingFileHandler(str(log_path), maxBytes=1e7)     # ~10MB
    handler.rotator = _gzip_rotator
    handler.namer = _gzip_namer

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(CustomFormatter(LOG_FMT, DATE_FMT))
    handler.set_name(name)
    if name not in [h.name for h in logger.handlers]:
        logger.addHandler(handler)
        logger.info("File logging initialized.")


def _setup_console_logging(logger):
    """
    Parameters
    ----------
    logger : :class:`logging.Logger`
    """
    name = "Console Handler"

    # Create the handler. Console handlers are easy.
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(CustomFormatter(LOG_FMT, DATE_FMT))
    handler.set_name(name)
    if name not in [h.name for h in logger.handlers]:
        logger.addHandler(handler)
        logger.info("Console logging initialized.")
