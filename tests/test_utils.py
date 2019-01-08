# -*- coding: utf-8 -*-
"""
"""
import pytest
from flask import current_app
from flask import Response

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
