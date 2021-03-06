# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime

import pytest
from flask import current_app
from flask import Response
from freezegun import freeze_time

from trendlines import orm
from trendlines import utils
from .test_orm import _hash_file


def test_adjust_jsonify_mimetype(app_context):
    var_name = "JSONIFY_MIMETYPE"
    old = current_app.config[var_name]
    assert current_app.config[var_name] != "foo"
    with utils.adjust_jsonify_mimetype('foo'):
        assert current_app.config[var_name] == 'foo'
    assert current_app.config[var_name] == old


@pytest.mark.parametrize("metric, expected", [
    ("foo", "#"),
    ("foo.bar", "foo"),
    ("foo.bar.baz", "foo.bar"),
])
def test_get_metric_parent(metric, expected):
    assert utils.get_metric_parent(metric) == expected


@pytest.mark.parametrize("data, expected", [
    (orm.Metric(metric_id=1, name="foo"),
     {"id": "foo", "parent": "#", "text": "foo", "metric_id": 1}),
    (orm.Metric(metric_id=2, name="foo.bar"),
     {"id": "foo.bar", "parent": "foo", "text": "foo.bar", "metric_id": 2}),
    (orm.Metric(metric_id=3, name="foo.bar.baz"),
     {"id": "foo.bar.baz", "parent": "foo.bar", "text": "foo.bar.baz",
      "metric_id": 3}),
])
def test_format_metric_for_jstree(test_request_context, data, expected):
    rv = utils.format_metric_for_jstree(data)
    assert rv == expected


@pytest.mark.parametrize("metrics, expected", [
    ([orm.Metric(metric_id=1, name="foo"),
      orm.Metric(metric_id=2, name="foo.bar")], [
        {"id": "foo", "parent": "#", "text": "foo",
         "metric_id": 1},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar",
         "metric_id": 2},
        ]
     ),
    ([orm.Metric(metric_id=1, name="foo.bar.baz")], [
        {"id": "foo", "parent": "#", "text": "foo", "metric_id": None},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar", "metric_id": None},
        {"id": "foo.bar.baz", "parent": "foo.bar", "text": "foo.bar.baz",
         "metric_id": 1},
        ]
     ),
    ([orm.Metric(metric_id=1, name="foo.bar"),
      orm.Metric(metric_id=2, name="foo.baz")], [
        {"id": "foo", "parent": "#", "text": "foo", "metric_id": None},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar",
         "metric_id": 1},
        {"id": "foo.baz", "parent": "foo", "text": "foo.baz",
         "metric_id": 2},
        ]
     ),
    ([orm.Metric(metric_id=1, name="foo"),
      orm.Metric(metric_id=2, name="foo.bar"),
      orm.Metric(metric_id=3, name="bar.baz.biz")], [
        {"id": "bar", "parent": "#", "text": "bar", "metric_id": None},
        {"id": "bar.baz", "parent": "bar", "text": "bar.baz", "metric_id": None},
        {"id": "bar.baz.biz", "parent": "bar.baz", "text": "bar.baz.biz",
         "metric_id": 3},
        {"id": "foo", "parent": "#", "text": "foo",
         "metric_id": 1},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar",
         "metric_id": 2},
       ]
     )
])
def test_build_jstree_data(test_request_context, metrics, expected):
    rv = utils.build_jstree_data(metrics)
    assert rv == expected


def test_format_data(raw_data):
    rv = utils.format_data(raw_data)
    assert isinstance(rv, dict)
    assert len(rv) == 2
    assert 'rows' in rv.keys()
    assert 'units' in rv.keys()
    assert isinstance(rv['rows'], list)
    assert len(rv['rows']) == 4
    data_0 = rv['rows'][0]
    assert isinstance(data_0, dict)
    # Why don't I just use an expected dict here? Because I haven't bothered
    # to freeze time on the `conftest.populated_db` fixture yet.
    assert "timestamp" in data_0.keys()
    assert "value" in data_0.keys()
    assert "id" in data_0.keys()
    assert "n" in data_0.keys()
    assert data_0['value'] == 15
    assert isinstance(data_0['timestamp'], str)
    try:
        #  datetime.fromisoformat(data_0['timestamp'])   # Python 3.7 only
        datetime.strptime(data_0['timestamp'], "%Y-%m-%dT%H:%M:%S")
    except Exception as err:
        pytest.fail("data['timestamp'] is not the correct format")


@freeze_time("2019-01-25T04:32:28Z")        # 1548390748
@pytest.mark.parametrize("value, expected", [
    ("metric 15",
     {"metric": "metric", "value": 15, "time": 1548390748}),
    (b"metric 19",
     {"metric": "metric", "value": 19, "time": 1548390748}),
    ("foo.bar 123.78 1546532070",
     {"metric": "foo.bar", "value": 123.78, "time": 1546532070}),
])
def test_parse_socket_data(value, expected):
    rv = utils.parse_socket_data(value)
    expected_keys = {"metric", "value", "time"}
    assert set(rv.keys()) == expected_keys
    assert rv == expected


@pytest.mark.parametrize("value", [
    "metric 15 apple",
    "foo bar 16",
    "aasdas 24.4523 ",
])
def test_parse_socket_data_raises_value_error(value):
    with pytest.raises(ValueError):
        utils.parse_socket_data(value)


@freeze_time("2019-01-25T04:32:28Z")
def test_backup_file(tmp_path):
    path = tmp_path / "foo.bar"
    path.write_text("hello")
    rv = utils.backup_file(path)
    assert rv.exists()
    assert rv.name == "foo.bar.20190125_043228"
    assert _hash_file(path) == _hash_file(rv)
