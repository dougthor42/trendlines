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
    assert d['title'] == "NOT_FOUND"
    assert "API error" in caplog.text


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
    assert d['title'] == "NOT_FOUND"
    assert "API error" in caplog.text


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
    assert d['metric']['metric_id'] == 7


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


def test_api_put_metric(client, populated_db):
    name = "foo.bar"
    data = {
        "name": name,
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    assert d['old_value']['units'] is None
    assert d['new_value']['units'] == "lines"


def test_api_put_metric_sets_other_values_to_none(client, populated_db):
    name = "with_everything"

    original = client.get("/api/v1/metric/{}".format(name))
    assert original.status_code == 200
    original = original.get_json()
    assert original['units'] == 'percent'
    assert original['upper_limit'] == 100.0
    assert original['lower_limit'] == 20.0

    data = {"name": name}
    rv = client.put("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 200

    new = client.get("/api/v1/metric/{}".format(name))
    assert new.status_code == 200
    new = new.get_json()

    assert new['units'] is None
    assert new['upper_limit'] is None
    assert new['lower_limit'] is None


def test_api_put_metric_not_found(client, populated_db):
    name = "missing"
    data = {
        "name": name,
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert name in d['detail']
    assert "does not exist" in d['detail']


def test_api_put_metric_duplicate_name(client, populated_db):
    new_name = "foo.bar"
    old_name = "old_data"
    data = {"name": new_name}
    rv = client.put("/api/v1/metric/{}".format(old_name), json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert old_name in d['detail']
    assert new_name in d['detail']
    assert "Unable to change metric name" in d['detail']


def test_api_put_metric_missing_name(client, populated_db):
    data = {"units": "goats"}
    rv = client.put("/api/v1/metric/foo", json=data)
    assert rv.status_code == 400
    assert rv.is_json
    d = rv.get_json()
    assert "Missing required" in d['detail']


def test_api_put_metric_idempotence(client, populated_db):
    # TODO: I don't think this is the right way to test idempotence...
    name = "foo.bar"
    data = {
        "name": name,
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    # First verify that things changed.
    assert d['old_value']['units'] != d['new_value']

    rv = client.put("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    # Then verify that they *didn't* change.
    assert d['old_value'] == d['new_value']


def test_api_patch_metric(client, populated_db):
    data = {"units": "pears"}
    rv = client.patch("/api/v1/metric/foo", json=data)
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    assert d['old_value']['units'] is None
    assert d['new_value']['units'] == "pears"
    assert 'name' not in d['old_value'].keys()
    assert 'name' not in d['new_value'].keys()
    assert 'lower_limit' not in d['old_value'].keys()
    assert 'lower_limit' not in d['new_value'].keys()


def test_api_patch_metric_doesnt_change_other_values(client, populated_db):
    name = "with_everything"
    original = client.get("/api/v1/metric/{}".format(name))
    assert original.status_code == 200
    original = original.get_json()
    assert original['units'] == 'percent'
    assert original['upper_limit'] == 100.0
    assert original['lower_limit'] == 20.0

    data = {"lower_limit": 0.2}
    rv = client.patch("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 200

    new = client.get("/api/v1/metric/{}".format(name))
    assert new.status_code == 200
    new = new.get_json()

    assert new['lower_limit'] == 0.2
    assert new['units'] == original['units']
    assert new['upper_limit'] == original['upper_limit']


def test_api_patch_metric_not_found(client, populated_db):
    name = "missing"
    data = {"units": "pears"}
    rv = client.patch("/api/v1/metric/{}".format(name), json=data)
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert name in d['detail']
    assert "does not exist" in d['detail']


def test_api_patch_metric_duplicate_name(client, populated_db):
    new_name = "foo.bar"
    old_name = "old_data"
    data = {"name": new_name}
    rv = client.patch("/api/v1/metric/{}".format(old_name), json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert old_name in d['detail']
    assert new_name in d['detail']
    assert "Unable to change metric name" in d['detail']
