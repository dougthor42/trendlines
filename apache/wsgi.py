#!/usr/local/bin/python3
import os

from trendlines import create_app

os.environ['TRENDLINES_CONFIG_FILE'] = "/data/trendlines.cfg"
application = create_app()
