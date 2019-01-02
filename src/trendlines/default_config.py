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

# Flask Builtins ################################
DEBUG = False
TESTING = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16MB
SECRET_KEY = b"change me"
