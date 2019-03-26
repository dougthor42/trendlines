# -*- coding: utf-8 -*-
"""
"""
from copy import deepcopy
from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from peewee import DoesNotExist
from peewee import IntegrityError

from trendlines import db
from trendlines import orm


def test_add_metric(app):
    rv = db.add_metric("foo", "bar")
    assert rv.name == "foo"
    assert rv.units == "bar"

    # Verify that we've actually written to the DB.
    assert len(db.Metric.select()) == 1


def test_add_metric_with_limits(app):
    rv = db.add_metric("foo", "bar", 5, 15)
    assert rv.name == "foo"
    assert rv.units == "bar"
    assert rv.upper_limit == 15
    assert rv.lower_limit == 5


def test_add_metric_with_upper_limit(app):
    rv = db.add_metric("foo", "bar", None, 15)
    assert rv.name == "foo"
    assert rv.units == "bar"
    assert rv.upper_limit == 15
    assert rv.lower_limit is None


def test_add_metric_with_lower_limit(app):
    rv = db.add_metric("foo", "bar", -16.33)
    assert rv.name == "foo"
    assert rv.units == "bar"
    assert rv.upper_limit is None
    assert rv.lower_limit == -16.33


def test_add_metric_with_invalid_limits_raises_value_error(caplog):
    with pytest.raises(ValueError):
        db.add_metric("foo", "bar", 16, -54.452)
    assert "upper_limit not greater than lower_limit" in caplog.text


@pytest.mark.parametrize("lower, upper", [
    ("hello", None),
    (None, "hello"),
    ("hello", "hello"),
    (object(), None),
    (int, str),
])
def test_add_metric_raises_type_error(caplog, lower, upper):
    with pytest.raises(TypeError):
        db.add_metric("foo", "bar", lower, upper)
    assert "Invalid type for limits" in caplog.text


def test_insert_datapoint(populated_db):
    rv = db.insert_datapoint("empty_metric", 15)
    assert rv.metric.metric_id == 1
    assert rv.value == 15
    assert isinstance(rv.timestamp, (int, float))

    new = db.DataPoint.select().where(db.DataPoint.metric_id == 1)
    assert len(new) == 1


def test_insert_datapoint_with_timestamp(populated_db):
    ts = 1546532070
    rv = db.insert_datapoint("empty_metric", 15, ts)
    assert rv.metric.metric_id == 1
    assert rv.value == 15
    assert isinstance(rv.timestamp, (int, float))

    new = db.DataPoint.select().where(db.DataPoint.metric_id == 1)
    assert len(new) == 1
    expected = _naive_utc_dt_from_posix_ts(ts)
    assert new[0].timestamp == expected


def test_get_data(populated_db):
    rv = db.get_data("empty_metric")
    assert len(rv) == 0
    rv = db.get_data("foo")
    assert len(rv) == 4
    assert isinstance(rv[0], orm.DataPoint)
    assert rv[0].value == 15
    assert rv[3].value == 9


@freeze_time("2019-01-03T16:14:30Z")        # 1546532070
def test_get_recent_data(populated_db):
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


def test_get_metrics(populated_db):
    rv = db.get_metrics()
    assert len(rv) == 6
    assert all(isinstance(x, orm.Metric) for x in rv)
    assert rv[0].name == "empty_metric"
    assert rv[1].metric_id == 2
    assert rv[3].units == "apples"


def test_get_units(populated_db):
    rv = db.get_units("metric_with_units")
    assert rv == "apples"

    rv = db.get_units("foo")
    assert rv is None


def test_get_datapoints(populated_db):
    rv = db.get_datapoints()
    assert len(rv) == 10
    assert isinstance(rv[0], orm.DataPoint)
    assert rv[2].value == 25
    assert rv[-1].value == 8


def test_get_datapoints_no_data(app):
    rv = db.get_datapoints()
    assert len(rv) == 0


def test_get_datapoint(populated_db):
    rv = db.get_datapoint(5)
    assert isinstance(rv, orm.DataPoint)
    assert rv.metric_id == 3
    assert rv.metric.name == "foo.bar"
    assert rv.value == 1
    # Check that the timestamp is naive
    # https://docs.python.org/3/library/datetime.html#datetime.timezone
    d = rv.timestamp
    assert (d.tzinfo is None) or (d.tzinfo.utcoffset(d) is None)


def test_get_datapoint_not_found(populated_db, caplog):
    with pytest.raises(DoesNotExist):
        db.get_datapoint(999)


def test_update_datapoint_metric_by_id(app, populated_db, caplog):
    original = deepcopy(db.get_datapoint(1))

    db.update_datapoint(1, metric=4)
    new = db.get_datapoint(1)
    assert new.datapoint_id == original.datapoint_id
    assert new.metric != original.metric
    assert new.metric.metric_id == 4
    assert new.value == original.value
    assert new.timestamp == original.timestamp
    assert "Updating datapoint" in caplog.text


def test_update_datapoint_metric_by_id_metric_not_found(app, populated_db):
    with pytest.raises(IntegrityError):
        db.update_datapoint(1, metric=99)


@pytest.mark.parametrize("val", [
    99,
    123,
    -1231203572.25215,
    0,
])
def test_update_datapoint_value_by_id(populated_db, val, caplog):
    # Get our original datapoint. DeepCopy avoids by-reference issues.
    original = deepcopy(db.get_datapoint(1))

    rv = db.update_datapoint(1, value=val)
    assert isinstance(rv, db.DataPoint)
    new = db.get_datapoint(1)
    assert rv == new
    assert new.datapoint_id == original.datapoint_id
    assert new.value == val
    assert new.timestamp == original.timestamp
    assert "Updating datapoint" in caplog.text


def test_update_datapoint_value_by_id_not_found(populated_db, caplog):
    with pytest.raises(DoesNotExist):
        db.update_datapoint(999, value=123)
    assert "Unable to find datapoint" in caplog.text
    assert "999" in caplog.text


def _naive_utc_dt_from_posix_ts(ts):
    """
    Return a naive datetime object for the given POSIX UTC timestamp.
    """
    new = datetime.fromtimestamp(ts, tz=timezone.utc)
    return new.replace(tzinfo=None)


@pytest.mark.parametrize("dt, expected", [
    (23425702, _naive_utc_dt_from_posix_ts(23425702)),
    (9483, _naive_utc_dt_from_posix_ts(9483)),
    ("now", _naive_utc_dt_from_posix_ts(1546532070)),
    (1, _naive_utc_dt_from_posix_ts(1)),
    #  (0, _naive_utc_dt_from_posix_ts(0)),  # See peewee#1875
])
@freeze_time("2019-01-03T16:14:30Z")        # 1546532070
def test_update_datapoint_timestamp_by_id(populated_db, dt, expected, caplog):
    # Get our original datapoint. DeepCopy avoids by-reference issues.
    original = deepcopy(db.get_datapoint(1))

    # Update the value
    rv = db.update_datapoint(1, timestamp=dt)
    assert isinstance(rv, db.DataPoint)

    # Verify the new value
    new = db.get_datapoint(1)
    assert rv == new
    assert new.datapoint_id == original.datapoint_id
    assert new.value == original.value
    assert isinstance(new.timestamp, datetime)
    assert new.timestamp == expected
    assert "Updating datapoint" in caplog.text


def test_update_datapoint_no_values_given(populated_db, caplog):
    original = deepcopy(db.get_datapoint(1))
    db.update_datapoint(1)
    new = db.get_datapoint(1)
    assert new == original
    assert "No new values given" in caplog.text


def test_update_datapoint_by_object(populated_db, caplog):
    datapoint = db.get_datapoint(1)
    original = deepcopy(datapoint)

    db.update_datapoint(datapoint, value=55)
    new = db.get_datapoint(1)
    assert new.datapoint_id == original.datapoint_id
    assert new.value == 55
    assert new.timestamp == original.timestamp
    assert "Updating datapoint" in caplog.text
    assert str(original) in caplog.text


def test_update_datapoint_by_object_does_not_exist(populated_db, caplog):
    datapoint = orm.DataPoint(metric_id=1, value=1, timestamp=1)
    with pytest.raises(DoesNotExist):
        db.update_datapoint(datapoint, value=55)


def test_delete_datapoint(populated_db, caplog):
    db.delete_datapoint(1)
    with pytest.raises(DoesNotExist):
        db.get_datapoint(1)
    assert "Deleting datapoint" in caplog.text

    datapoint = db.get_datapoint(5)
    db.delete_datapoint(datapoint)
    with pytest.raises(DoesNotExist):
        db.get_datapoint(5)
    assert str(datapoint) in caplog.text


def test_delete_datpoint_does_not_exist(populated_db):
    with pytest.raises(DoesNotExist):
        db.delete_datapoint(999)

    missing = orm.DataPoint(value=50)
    with pytest.raises(DoesNotExist):
        db.delete_datapoint(missing)
