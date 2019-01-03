# -*- coding: utf-8 -*-
"""
"""

import pytest


from trendlines import routes


def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_index_with_data(client, populated_db):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"empty_metric" in rv.data
    assert b"foo.bar" in rv.data


@pytest.mark.xfail(reason="Needs code updates")
def test_plot(client):
    rv = client.get("/plot/foo")
    assert rv.status_code == 404


def test_plot_with_data(client, populated_db):
    rv = client.get("/plot/foo")
    assert rv.status_code == 200
    assert b"foo" in rv.data
    assert b'<div id="graph"' in rv.data


def test_api_add(client):
    data = {"metric": "test", "value": 10}
    rv = client.post("/api/v1/add", json=data)
    assert rv.status_code == 201
    assert b"Added DataPoint to Metric" in rv.data


def test_api_add_with_missing_key(client):
    data = {"value": 10}
    rv = client.post("/api/v1/add", json=data)
    assert rv.status_code == 400
    assert b"Missing required key. Required keys are:" in rv.data


def test_format_data(raw_data):
    rv = routes.format_data(raw_data)
    assert isinstance(rv, dict)
    assert len(rv) == 1
    assert 'rows' in rv.keys()
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
