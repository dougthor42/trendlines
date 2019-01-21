# -*- coding: utf-8 -*-
"""
"""
import pytest

from trendlines import routes


def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200


@pytest.mark.xfail(reason="Need to figure out the AJAX testing.")
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
    d = rv.get_json()
    assert d['units'] == None
    d = d['rows']
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
