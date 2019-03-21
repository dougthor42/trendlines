# -*- coding: utf-8 -*-
import os
from traceback import format_exc

from flask import Flask
from flask import g
from peewee import OperationalError

from trendlines import _logging
from trendlines import logger
from trendlines import routes
from trendlines import orm

CFG_VAR = "TRENDLINES_CONFIG_FILE"

def create_app():
    """
    Primary application factory.
    """
    _logging.setup_logging(logger)

    logger.debug("Creating app.")
    app = Flask(__name__)
    app.config.from_object('trendlines.default_config')

    try:
        app.config.from_envvar(CFG_VAR)
        logger.info("Loaded config file '%s'" % os.environ[CFG_VAR])
    except FileNotFoundError:
        msg = "Failed to load config file. The file %s='%s' was not found."
        logger.warning(msg % (CFG_VAR, os.environ[CFG_VAR]))
    except RuntimeError as err:
        # Flask's error for missing env var is sufficient.
        logger.warning(str(err))
    except Exception as err:
        logger.warning("An unknown error occured while reading from the"
                       " config file. See debug stack trace for details.")
        logger.debug(format_exc())


    logger.debug("Registering blueprints.")
    app.register_blueprint(routes.pages)

    # Initialize flask-rest-api for OpenAPI (Swagger) documentation
    routes.api_class.init_app(app)
    routes.api_class.register_blueprint(routes.api)
    routes.api_class.register_blueprint(routes.api_datapoint)
    routes.api_class.register_blueprint(routes.api_metric)

    # Create the database file and populate initial tables if needed.
    orm.create_db(app.config['DATABASE'])

    # If I redesign the architecture a bit, then these could be moved so
    # that they only act on the `api` blueprint instead of the entire app.
    #
    # Also, note that this is safe for multiple simultaneous requests, since
    # the database object is thread local:
    #   "Peewee uses thread local storage to manage connection state, so
    #    this pattern can be used with multi-threaded WSGI servers."
    # http://docs.peewee-orm.com/en/latest/peewee/example.html#establishing-a-database-connection
    @app.before_request
    def before_request():
        """
        Attach the ORM to the flask ``g`` object before every request.

        Why not just use ``from orm import db`` most of the time? Well, it's
        because:
        (a) that's how I'm used to from SQLAlchemy
        (b) I may need ``db`` somewhere where I *can't* import ``orm``
        (c) because that's how the example PeeWee project is set up. /shrug.
            https://github.com/coleifer/peewee/blob/master/examples/twitter/app.py#L152
        """
        g.db = orm.db
        try:
            g.db.connect()
        except OperationalError:
            pass

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

    return app
