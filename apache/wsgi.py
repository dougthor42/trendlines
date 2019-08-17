#!/usr/local/bin/python3
import os

from trendlines import create_app

os.environ['TRENDLINES_CONFIG_FILE'] = "/data/trendlines.cfg"
application = create_app()

class PrefixMiddleware:
    def __init__(self, app, prefix=""):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"].startswith(self.prefix):
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix):]
            environ["SCRIPT_NAME"] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response("404", [("Content-Type", "text/plain")])
            return ["This URL does not belong to the app.".encode()]

# Handle cases where we're behind a proxy that is modifying our URL.
if application.config.get('URL_PREFIX', None) is not None:
    application.wsgi_app = PrefixMiddleware(application.wsgi_app,
            prefix=application.config["URL_PREFIX"],
        )
