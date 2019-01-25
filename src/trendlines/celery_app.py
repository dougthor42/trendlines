# -*- coding: utf-8 -*-
"""
Create the celery application.

Only used because I have to set the TRENDLINES_CONFIG_FILE environment
variable and I haven't bothered to figure out a better way.
"""
import os

from trendlines.celery_factory import create_celery

os.environ['TRENDLINES_CONFIG_FILE'] = "/data/trendlines.cfg"
celery = create_celery()
