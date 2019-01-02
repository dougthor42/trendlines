# -*- coding: utf-8 -*-
"""
"""

import pytest
from freezegun import freeze_time

from trendlines import db
from trendlines import orm


def test_add_metric(app):
    rv = db.add_metric("foo", "bar")
    assert rv.name == "foo"
    assert rv.units == "bar"

    # Verify that we've actually written to the DB.
    assert len(db.Metric.select()) == 1


def test_add_data_point(app, populated_db):
    rv = db.add_data_point("empty_metric", 15)
    assert rv.metric.metric_id == 1
    assert rv.value == 15
    assert isinstance(rv.timestamp, (int, float))

    new = db.DataPoint.select().where(db.DataPoint.metric_id == 1)
    assert len(new) == 1


def test_get_data(app, populated_db):
    rv = db.get_data("empty_metric")
    assert len(rv) == 0
    rv = db.get_data("foo")
    assert len(rv) == 4
    assert isinstance(rv[0], orm.DataPoint)
    assert rv[0].value == 15
    assert rv[3].value == 9


@freeze_time("2019-01-03T16:14:30Z")        # 1546532070
def test_get_recent_data(app, populated_db):
    """
    Our data from the populated_db fixture has the following timestamps::

      Timestamp             Seconds from FreezeGun
      2018-12-20 15:53:56Z  1210834
      2019-01-03 16:13:23Z  67
      2019-01-03 16:14:27Z  3

    """
    # Everything since the dawn of (linux) time!
    rv = db.get_recent_data("old_data", 1e10)
    assert len(rv) == 4

    # Last 2 values
    rv = db.get_recent_data("old_data", 120)
    assert len(rv) == 2
    assert isinstance(rv[0], orm.DataPoint)
    assert rv[0].value == 5

    # Last value
    rv = db.get_recent_data("old_data", 5)
    assert len(rv) == 1
    assert rv[0].value == 8


def test_get_metrics(app, populated_db):
    rv = db.get_metrics()
    assert len(rv) == 5
    assert all(isinstance(x, orm.Metric) for x in rv)
    assert rv[0].name == "empty_metric"
    assert rv[1].metric_id == 2
    assert rv[3].units == "apples"
