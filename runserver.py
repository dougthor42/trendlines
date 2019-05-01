# -*- coding: utf-8 -*-
import os
from pathlib import Path

import click

import trendlines.orm as orm
from trendlines.app_factory import create_app

PORT = 5000


def make_db_from_orm():
    """
    Make the database directly from the ORM rather than via migrations.
    """
    print("making...")
    orm.db.init("internal.db", pragmas=orm.DB_OPTS)
    orm.db.connect()
    orm.db.create_tables([orm.Metric, orm.DataPoint])
    orm.db.close()
    print("Done.")


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
@click.option("--db-from-orm", is_flag=True)
def main(db_from_orm):
    if db_from_orm:
        make_db_from_orm()
    else:
        runserver()


if __name__ == "__main__":
    main()
