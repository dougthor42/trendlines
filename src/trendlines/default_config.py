# -*- coding: utf-8 -*-
"""
Default configuration settings.

These settings are suitable for a locally-run production-like
environment using SQLite.

When converting to a production environment, the only *requirement* is to
change the value of SECRET_KEY. Everything else should be suitable for
running in production. I hope.
"""

# What database to use. Valid options are: "sqlite"
DB_TYPE = "sqlite"

# The database file to use. Ignored if DB_TYPE is not "sqlite"
DATABASE = "./internal.db"

# Set this value to insert a prefix into any generaged URLs. Mainly used when
# running behind a proxy that is adjusting URLs.
#URL_PREFIX = "/trendlines"

# Celery stuff. See here for names:
# http://docs.celeryproject.org/en/latest/userguide/configuration.html
broker_url = "redis://redis"

# Socket stuff.
TARGET_HOST = "0.0.0.0"
TRENDLINES_API_URL = "http://trendlines/api/v1/data"
TCP_PORT = 9999
UDP_PORT = 9999

# Flask Builtins ################################
DEBUG = False
TESTING = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16MB
SECRET_KEY = b"change me"
