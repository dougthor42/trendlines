#!/usr/local/bin/python3
import os

from werkzeug.wsgi import DispatcherMiddleware

from trendlines import create_app

os.environ['TRENDLINES_CONFIG_FILE'] = "/data/trendlines.cfg"
application = create_app()

# Handle cases where we're behind a proxy that is modifying our URL.
#  if application.config.get('URL_PREFIX', None) is not None:
    #  application = DispatcherMiddleware(
        #  application,
        #  {application.config['URL_PREFIX']: application}
    #  )
