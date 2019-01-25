# -*- coding: utf-8 -*-
"""
Celery factory and related functions.
"""
import errno
import os
import socketserver
import types
from pathlib import Path
from traceback import format_exc

import requests
from celery import Celery
from celery.exceptions import ImproperlyConfigured

from trendlines import utils
from trendlines import logger

# TODO: queueing?

CFG_VAR = "TRENDLINES_CONFIG_FILE"


def config_from_envvar(app, var_name, silent=False):
    """
    Load celery config from an envvar that points to a python config file.

    Basically this:

        config_from_pyfile(os.environ['YOUR_APP_SETTINGS'])

    Example:
        >>> os.environ['CELERY_CONFIG_MODULE'] = './some_dir/config_file.cfg'
        >>> config_from_envvar(celery, 'CELERY_CONFIG_MODULE')

    Arguments:
        app (Celery app instance): The celery app to update
        var_name (str): The env var to use.
        silent (bool): If true then import errors will be ignored.

    Shamelessly taken from Flask. Like, almost exactly. Thanks!
    https://github.com/pallets/flask/blob/74691fbe0192de1134c93e9821d5f8ef65405670/flask/config.py#L88
    """
    rv = os.environ.get(var_name)
    if not rv:
        if silent:
            return False
        raise RuntimeError('The environment variable %r is not set'
                           ' and as such configuration could not be'
                           ' loaded. Set this variable to make it'
                           ' point to a configuration file.' % var_name)
    return config_from_pyfile(app, rv, silent=silent)


def config_from_pyfile(app, filename, silent=False):
    """
    Mimics Flask's config.from_pyfile()

    Allows loading a separate, perhaps non `.py`, file into Celery.

    Example:
        >>> config_from_pyfile(celery, './some_dir/config_file.cfg')

    Arguments:
        app (Celery app instance): The celery app to update
        filename (str): The file to load.
        silent (bool): If true then import errors will be ignored.

    Also shamelessly taken from Flask:
    https://github.com/pallets/flask/blob/74691fbe0192de1134c93e9821d5f8ef65405670/flask/config.py#L111
    """
    filename = str(Path(filename).resolve())
    d = types.ModuleType('config')
    d.__file__ = filename

    try:
        with open(filename, 'rb') as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if silent and e.errno in(errno.ENOENT, errno.EISDIR, errno.ENOTDIR):
            return False
        e.strerror = "Unable to load config file (%s)" % e.strerror
        raise

    # Remove any hidden attributes: __ and _
    for k in list(d.__dict__.keys()):
        if k.startswith("_"):
            del d.__dict__[k]

    logger.debug("Config values: %s" % d.__dict__)
    app.conf.update(d.__dict__)
    return True


def create_celery():
    celery = Celery(__name__, autofinalize=False)

    # Pull config from file. This is basically the same as what is
    # done in app_factory.create_app()
    celery.config_from_object('trendlines.default_config')
    try:
        config_from_envvar(celery, CFG_VAR)
        logger.info("Loaded config file '%s'" % os.environ[CFG_VAR])
    except FileNotFoundError:
        msg = "Failed to load config file. The file %s='%s' was not found."
        logger.warning(msg % (CFG_VAR, os.environ[CFG_VAR]))
    except (RuntimeError, ImproperlyConfigured) as err:
        # Celery's error for missing env var is sufficient.
        logger.warning(str(err))
    except Exception as err:
        logger.warning("An unknown error occured while reading from the"
                       " config file. See debug stack trace for details.")
        logger.debug(format_exc())


    UDP_PORT = celery.conf['UDP_PORT']
    TCP_PORT = celery.conf['TCP_PORT']
    HOST = celery.conf['TARGET_HOST']
    URL = celery.conf['TRENDLINES_API_URL']
    celery.finalize()
    logger.debug("Celery has been finalized.")


    class TCPHandler(socketserver.BaseRequestHandler):
        def handle(self):
            data = self.request.recv(1024).strip()
            try:
                parsed = utils.parse_socket_data(data)
                logger.debug("TCP: {}".format(parsed))
            except ValueError:
                logger.warn("TCP: Failed to parse `%s`." % data)
                return

            try:
                r = requests.post(URL, json=parsed)
                logger.info(r.status_code)
            except Exception:
                raise
            self.request.sendall(b"accepted")

    @celery.task
    def listen_to_tcp():
        hp = (HOST, TCP_PORT)
        logger.info("listening for TCP on %s:%s" % hp)
        with socketserver.TCPServer(hp, TCPHandler) as server:
            server.serve_forever()

    # Start our tasks
    logger.debug("Starting tasks")
    #  listen_to_udp.delay()
    listen_to_tcp.delay()

    return celery
