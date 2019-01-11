# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime

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
    rv = client.post("/api/v1/data", json=data)
    assert rv.status_code == 201
    assert b"Added DataPoint to Metric" in rv.data


def test_api_add_with_missing_key(client):
    data = {"value": 10}
    rv = client.post("/api/v1/data", json=data)
    assert rv.status_code == 400
    assert b"Missing required key. Required keys are:" in rv.data


def test_api_get_data_as_json(client, populated_db):
    rv = client.get("/api/v1/data/foo")
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()['rows']
    assert d[0]['n'] == 0
    assert d[0]['value'] == 15
    assert d[3]['value'] == 9


def test_api_get_data_as_json_metric_not_found(client):
    rv = client.get("/api/v1/data/missing")
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert 'type' in d.keys()
    assert d['status'] == 404
    assert 'does not exist' in d['detail']


def test_api_get_data_as_json_no_data_for_metric(client, populated_db):
    rv = client.get("/api/v1/data/empty_metric")
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert 'type' in d.keys()
    assert d['status'] == 404
    assert 'No data exists for metric' in d['detail']


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
    assert isinstance(data_0['timestamp'], str)
    try:
        #  datetime.fromisoformat(data_0['timestamp'])   # Python 3.7 only
        datetime.strptime(data_0['timestamp'], "%Y-%m-%dT%H:%M:%S")
    except Exception as err:
        pytest.fail("data['timestamp'] is not the correct format")
