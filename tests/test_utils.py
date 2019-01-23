# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime

import pytest
from flask import current_app
from flask import Response
from freezegun import freeze_time

from trendlines import utils


@pytest.fixture
def rfc_object():
    return utils.Rfc7807ErrorResponse(
        type_="http://too.bad",
        title="Some Error",
        status=400,
        detail="There are no details.",
        instance="foo",
        account="yours",
        balance=30,
    )


def test_rfc_error_response_as_dict(rfc_object):
    rv = rfc_object.as_dict()
    assert isinstance(rv, dict)
    assert len(rv.keys()) == 7
    assert rv['balance'] == 30

    rfc_object.detail = None
    rv = rfc_object.as_dict()
    assert len(rv.keys()) == 6
    assert 'detail' not in rv.keys()


def test_rfc_error_response_as_response(app_context, rfc_object):
    rv = rfc_object.as_response()
    assert isinstance(rv, Response)
    assert rv.is_json
    assert rv.mimetype == "application/problem+json"


def test_rfc_error_response_content_type(rfc_object):
    rv = rfc_object.content_type
    assert rv == "application/problem+json"

    # Make sure we can't set the content_type easily.
    with pytest.raises(AttributeError):
        rfc_object.content_type = "foo"

    # even setting the "private" attribute doesn't change things.
    rfc_object._content_type = "foo"
    rv = rfc_object.content_type
    assert rv == "application/problem+json"


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
    ("foo", {"id": "foo", "parent": "#", "text": "foo", "is_link": True}),
    ("foo.bar", {"id": "foo.bar", "parent": "foo", "text": "foo.bar",
                 "is_link": True}),
    ("foo.bar.baz", {"id": "foo.bar.baz", "parent": "foo.bar",
                     "text": "foo.bar.baz", "is_link": True}),
])
def test_format_metric_for_jstree(data, expected):
    rv = utils.format_metric_for_jstree(data)
    assert rv == expected


@pytest.mark.parametrize("metrics, expected", [
    (["foo", "foo.bar"], [
        {"id": "foo", "parent": "#", "text": "foo", "is_link": True},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar", "is_link": True},
        ]
     ),
    (["foo.bar.baz"], [
        {"id": "foo", "parent": "#", "text": "foo", "is_link": False},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar",
         "is_link": False},
        {"id": "foo.bar.baz", "parent": "foo.bar", "text": "foo.bar.baz",
         "is_link": True},
        ]
     ),
    (["foo.bar", "foo.baz"], [
        {"id": "foo", "parent": "#", "text": "foo", "is_link": False},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar", "is_link": True},
        {"id": "foo.baz", "parent": "foo", "text": "foo.baz", "is_link": True},
        ]
     ),
    (["foo", "foo.bar", "bar.baz.biz"], [
        {"id": "bar", "parent": "#", "text": "bar", "is_link": False},
        {"id": "bar.baz", "parent": "bar", "text": "bar.baz", "is_link": False},
        {"id": "bar.baz.biz", "parent": "bar.baz", "text": "bar.baz.biz",
         "is_link": True},
        {"id": "foo", "parent": "#", "text": "foo", "is_link": True},
        {"id": "foo.bar", "parent": "foo", "text": "foo.bar", "is_link": True},
       ]
     )
])
def test_build_jstree_data(metrics, expected):
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
