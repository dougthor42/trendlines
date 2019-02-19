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


def test_api_get_metric_as_json(client, populated_db, caplog):
    rv = client.get("/api/v1/metric/foo")
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    print(d)
    assert d['metric_id'] == 2
    assert "API: get metric" in caplog.text


def test_api_get_metric_as_json_not_found(client, populated_db, caplog):
    metric = "querty"
    rv = client.get("/api/v1/metric/{}".format(metric))
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert metric in d['detail']
    assert d['title'] == "Metric not found"
    assert "API error:" in caplog.text


def test_api_delete_metric(client, populated_db):
    metric = "foo.bar"
    rv = client.delete("/api/v1/metric/{}".format(metric))
    assert rv.status_code == 204

    # Verify it's actually been deleted
    after = client.get("/api/v1/metric/{}".format(metric))
    assert after.status_code == 404


def test_api_delete_metric_not_found(client, populated_db, caplog):
    metric = "missing"
    rv = client.delete("/api/v1/metric/{}".format(metric))
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert metric in d['detail']
    assert d['title'] == "Metric not found"
    assert "API error:" in caplog.text


def test_api_post_metric(client, populated_db):
    metric = "new"
    units = "some units"
    upper_limit = 15.3
    lower_limit = 1.24
    data = {"name": metric,
            "units": units,
            "upper_limit": upper_limit,
            "lower_limit": lower_limit,
            }
    rv = client.post("/api/v1/metric", json=data)
    assert rv.status_code == 201
    assert rv.is_json
    d = rv.get_json()
    assert metric in d['message']
    assert d['metric']['name'] == metric
    assert d['metric']['lower_limit'] == lower_limit
    assert d['metric']['metric_id'] == 6


def test_api_post_metric_already_exists(client, populated_db):
    metric = "foo.bar"
    data = {"name": metric}
    rv = client.post("/api/v1/metric", json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert "already exists" in d['detail']


def test_api_post_metric_missing_key(client, populated_db):
    data = {"units": "percent"}
    rv = client.post("/api/v1/metric", json=data)
    assert rv.status_code == 400
    assert rv.is_json
    d = rv.get_json()
    assert "Missing required" in d['detail']
