# -*- coding: utf-8 -*-
"""
"""
import logging
import sys


def setup_logging(logger, to_console=True, to_file=False, log_path=None):
    """
    Setup logging for this project.

    Parameters
    ----------
    logger : :class:`loguru.Logger`
        The Loguru logger object.
    to_console : bool, optional
        If ``True``, enable logging to the console.
    to_file : bool, optional
        If ``True``, enable logging to a file.
    log_path : str, optional
        The file to log to, if ``to_file`` is ``True``.
    """
    if to_console:
        _setup_console_logging(logger)
    if to_file:
        _setup_file_logging(logger, log_path)


def _setup_file_logging(logger, log_path):
    """
    Parameters
    ----------
    logger : :class:`loguru.logger`
        The logger to modify
    log_path : :class:`pathlib.Path`
        The file and path to log to.
    """
    logger.add(log_path,
               rotation="1 week",
               retention="20 weeks",
               compression="tar.gz",
               format='<green>{time:YYYY-MM-DD HH:mm:ss.SSSZZ}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
               )

    logger.info("File logging initialized.")


def _setup_console_logging(logger):
    """
    Parameters
    ----------
    logger : :class:`loguru.logger`
        The logger instance to modify.
    """
    # This is only here in case I decide I want to make changes. For now
    # it's a noop.
    logger.info("Console logging initialized.")
