# -*- coding: utf-8 -*-
import os
from pathlib import Path

import click

import trendlines.orm as orm
from trendlines.app_factory import create_app

PORT = 5000


def runserver():
    # Load our configuration. We're using pathlib and `.resolve()` because
    # Flask's working dir is src/trendlines and uses that when running
    # `app.config.from_envvar`, so the path it attemps to load is
    # `/proj_folder/src/trendlines/config/localhost.cfg` if `cfg_file` is not
    # absolute.
    cfg_file = Path('./config/localhost.cfg')
    os.environ['TRENDLINES_CONFIG_FILE'] = str(cfg_file.resolve())

    app = create_app()
    app.run(debug=True, port=PORT, use_reloader=True)


@click.command()
def main(db_from_orm):
    runserver()


if __name__ == "__main__":
    main()
