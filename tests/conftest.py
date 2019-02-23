# -*- coding: utf-8 -*-
"""
Global PyTest fixtures.
"""
import logging
from pathlib import Path

import pytest
from _pytest.logging import caplog as _caplog

from trendlines import db
from trendlines import logger
from trendlines.app_factory import create_app
from trendlines.app_factory import create_db
from trendlines.orm import DataPoint
from trendlines.orm import Metric


@pytest.fixture
def caplog(_caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)
    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)


@pytest.fixture
def app():
    """
    A test app.

    Needed to do things like creating a test client.
    """
    db_file = Path("test.db")

    # Unlink the db_file on setup instead of on teardown. This is so we can
    # check what's in the database after a test has run.
    try:
        db_file.unlink()
    except FileNotFoundError:
        pass

    app = create_app()

    # Since the `create_db` function modifies orm.db directly, we can simply
    # call it here. I guess *technically* what's happening is whatever
    # DATABASE value set in default_config.py or TRENDLINES_CONFIG_FILE is
    # actually made first, but I don't think I really care right now.
    create_db(str(db_file))
    app.testing = True
    yield app


@pytest.fixture
def populated_db():
    # XXX: Should this be using my functions or should it use pure PeeWee
    # stuff like `DataPoint.create(metric=1, value=15, timestamp=1546450008)`?
    db.add_metric("empty_metric", "units")
    db.add_metric("foo")
    db.add_metric("foo.bar")
    db.add_metric("metric_with_units", "apples")
    db.add_metric("old_data")
    db.add_metric("with_everything", "percent", 20, 100)
    db.add_data_point("foo", 15)
    db.add_data_point("foo", 17)
    db.add_data_point("foo", 25)
    db.add_data_point("foo", 9)
    db.add_data_point("foo.bar", 1)
    db.add_data_point("foo.bar", -2)
    db.add_data_point("old_data", 0, 0)             # 1970-01-01T00:00:00Z
    db.add_data_point("old_data", 1, 1545321236)    # 2018-12-20T15:53:56Z
    db.add_data_point("old_data", 5, 1546532003)    # 2019-01-03T16:13:23Z
    db.add_data_point("old_data", 8, 1546532067)    # 2019-01-03T16:14:27Z


@pytest.fixture
def raw_data(app, populated_db):
    """
    Provide the raw data as returned by :func:`db.get_data`.
    """
    return db.get_data("foo")


@pytest.fixture
def raw_metric(app, populated_db):
    """
    Provide the raw metric data as return by a Metric query"
    """
    return db.Metric.get(db.Metric.name == 'foo')


@pytest.fixture
def client(app):
    """
    A test client.

    Needed for things like getting route pages.
    """
    client = app.test_client()
    yield client


@pytest.fixture
def app_context(app):
    """
    An app context.

    """
    with app.app_context():
        yield app
