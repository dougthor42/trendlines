# -*- coding: utf-8 -*-
"""
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from peewee import OperationalError

from trendlines import orm


def test_metric_str():
    m = orm.Metric(name="foo", units="bar")
    assert str(m) == "<Metric: None, foo, units=bar>"


def test_datapoint_str():
    m = orm.Metric(name="foo")
    d = orm.DataPoint(metric=m, value=15.34, timestamp=10)
    assert str(d) == "<DataPoint: None, foo, 15.34, 10>"


def test_create_db(tmp_path):
    path = tmp_path / "foo.db"
    orm.create_db(str(path))
    # if the function worked the file should now exist.
    assert path.exists()


@patch("trendlines.orm.db.connect", MagicMock(side_effect=OperationalError))
def test_create_db_logs_and_raises_operational_error(caplog):
    with pytest.raises(OperationalError):
        orm.create_db("foo")

    assert "Unable to open database file" in caplog.text
    assert "foo" in caplog.text
