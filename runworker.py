# -*- coding: utf-8 -*-
"""
Run a celery worker.
"""
import os
from pathlib import Path

from celery.bin import worker

from trendlines.celery_factory import create_celery

# Load our configuration. We're using pathlib and `.resolve()` because
# Flask's working dir is src/trendlines and uses that when running
# `app.config.from_envvar`, so the path it attemps to load is
# `/proj_folder/src/trendlines/config/localhost.cfg` if `cfg_file` is not
# absolute.
cfg_file = Path('./config/localhost.cfg')
os.environ['TRENDLINES_CONFIG_FILE'] = str(cfg_file.resolve())

#  app.worker_main()
celery = create_celery()
worker = worker.worker(app=celery)
worker.run()
