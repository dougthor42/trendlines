# -*- coding: utf-8 -*-
"""
Global PyTest fixtures.
"""
import logging
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from _pytest.logging import caplog as _caplog

from trendlines import db
from trendlines import logger
from trendlines.app_factory import create_app
from trendlines.orm import create_db
from trendlines.orm import DataPoint
from trendlines.orm import Metric


@pytest.fixture
def caplog(_caplog):
    """
    Overwirte pytest's caplog to work with loguru.

    See https://github.com/Delgan/loguru/issues/59
    """
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)
    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)


@pytest.fixture
def app(tmp_path):
    """
    A test app.

    Needed to do things like creating a test client.
    """
    db_file = Path(tmp_path) / "test.db"

    # Mock out create_db - we'll do it later. If we let it happen now, then
    # a database will be made using the `app.config['DATABASE']` value,
    # which we don't want. (since that'll typically be `./internal.db`)
    with patch('trendlines.orm.create_db', MagicMock()):
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
    db.insert_datapoint("foo", 15)
    db.insert_datapoint("foo", 17)
    db.insert_datapoint("foo", 25)
    db.insert_datapoint("foo", 9)
    db.insert_datapoint("foo.bar", 1)
    db.insert_datapoint("foo.bar", -2)
    db.insert_datapoint("old_data", 0, 0)             # 1970-01-01T00:00:00Z
    db.insert_datapoint("old_data", 1, 1545321236)    # 2018-12-20T15:53:56Z
    db.insert_datapoint("old_data", 5, 1546532003)    # 2019-01-03T16:13:23Z
    db.insert_datapoint("old_data", 8, 1546532067)    # 2019-01-03T16:14:27Z


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


@pytest.fixture
def test_request_context(app):
    with app.test_request_context():
        yield app
