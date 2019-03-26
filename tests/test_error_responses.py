# -*- coding: utf-8 -*-
"""
"""
import pytest
from flask import current_app
from flask import Response
from freezegun import freeze_time

from trendlines import error_responses
from trendlines.error_responses import ErrorResponse


@pytest.fixture
def rfc_object():
    return error_responses.Rfc7807ErrorResponse(
        type_="http://too.bad",
        title="Some Error",
        status=400,
        detail="There are no details.",
        instance="foo",
        account="yours",
        balance=30,
    )


@pytest.mark.parametrize("value",
    [item for item in error_responses.ErrorResponseType]
)
def test_error_response_type_enum(value):
    assert "_" not in str(value)
    assert str(value).islower()
    assert value.url.startswith("http")


def test_error_response(app_context, caplog):
    rv = error_responses.error_response(
        404,
        error_responses.ErrorResponseType.NOT_FOUND,
        "foo"
    )
    assert isinstance(rv, tuple)
    assert len(rv) == 2
    assert rv[0].is_json
    assert "foo" in caplog.text


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


# TODO: Should I mock out the `error_response` function here?
@pytest.mark.parametrize("method, args", [
    (ErrorResponse.metric_not_found, ("foo", )),
    (ErrorResponse.metric_has_no_data, ("foo", )),
    (ErrorResponse.metric_already_exists, ("foo", )),
    (ErrorResponse.unique_metric_name_required, ("foo", "bar")),
    (ErrorResponse.missing_required_key, ("foo", )),
    (ErrorResponse.missing_required_key, (["foo", "bar"], )),
    (ErrorResponse.no_data, None),
])
def test_error_response_class_methods(app_context, caplog, method, args):
    if args is None:
        rv = method()
    else:
        rv = method(*args)
    assert isinstance(rv, tuple)
    assert len(rv) == 2
    assert rv[0].is_json
