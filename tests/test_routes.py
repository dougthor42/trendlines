# -*- coding: utf-8 -*-
"""
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from trendlines import routes
from trendlines import orm


API_BASE = "/api/v1"

def metric_url(metric_id=None):
    """
    Helper to generate the metric url with ID.

    Examples
    --------
    >>> metric_url()
    "/api/v1/metric"
    >>> metric_url(5)
    "/api/v1/metric/5"
    """
    if metric_id is not None:
        return API_BASE + "/metric/{}".format(metric_id)
    return API_BASE + "/metric"


def datapoint_url(datapoint_id=None):
    """
    Helper to generate the metric url with ID.

    Examples
    --------
    >>> datapoint_url()
    "/api/v1/datapoint"
    >>> datapoint_url(5)
    "/api/v1/datapoint/5"
    """
    if datapoint_id is not None:
        return API_BASE + "/datapoint/{}".format(datapoint_id)
    return API_BASE + "/datapoint"


def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_index_with_data(client, populated_db):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"empty_metric" in rv.data
    assert b"foo.bar" in rv.data


@pytest.mark.xfail(
    reason="JS callbacks are async: plotly div not populated immediatly"
)
def test_plot_with_data_by_name(client, populated_db):
    rv = client.get("/plot/foo")
    assert rv.status_code == 200
    assert b"foo" in rv.data
    assert b'<div id="graph"' in rv.data
    # TODO: make this work. Issue is JS callbacks.
    #  assert b'<div class="plot-container plotly">' in rv.data


@pytest.mark.xfail(
    reason="JS callbacks are async: plotly div not populated immediatly"
)
def test_plot_with_data_by_id(client, populated_db):
    rv = client.get("/plot/1")
    assert rv.status_code == 200
    assert b"foo" in rv.data
    assert b'<div id="graph"' in rv.data
    # TODO: make this work. Issue is JS callbacks.
    #  assert b'<div class="plot-container plotly">' in rv.data


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


def test_api_get_data_by_id(client, populated_db):
    rv = client.get("/api/v1/data/2")
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


@pytest.mark.usefixtures('populated_db')
class TestDataPoint(object):
    def test_get(self, client):
        rv = client.get(datapoint_url())
        assert rv.status_code == 200
        assert rv.is_json
        d = rv.get_json()
        assert set(d.keys()) == {'count', 'next', 'prev', 'results'}
        assert len(d['results']) == 10
        assert d['results'][0]['value'] == 15

    def test_post(self, client):
        value = 15
        timestamp = 12451245
        data = {'metric_id': 1,
                'value': value,
                'timestamp': timestamp,
                }

        rv = client.post(datapoint_url(), json=data)
        assert rv.status_code == 201
        assert rv.is_json
        d = rv.get_json()
        assert isinstance(d['datapoint_id'], int)
        assert d['value'] == value

    @pytest.mark.parametrize('missing_key', ['metric_id', 'value'])
    def test_post_missing_key(self, client, missing_key):
        data = {'metric_id': 4, 'value': 101}
        data.pop(missing_key)
        rv = client.post(datapoint_url(), json=data)
        assert rv.status_code == 400
        assert rv.is_json
        d = rv.get_json()
        assert missing_key in d['detail']

    def test_post_metric_not_found(self, client):
        metric_id = 99
        data = {'metric_id': metric_id, 'value': 101}
        rv = client.post(datapoint_url(), json=data)
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(metric_id) in d['detail']


@pytest.mark.usefixtures('populated_db')
class TestDataPointById(object):
    def test_get(self, client):
        datapoint_id = 6
        rv = client.get(datapoint_url(datapoint_id))
        assert rv.status_code == 200
        assert rv.is_json
        d = rv.get_json()
        assert d['value'] == -2
        assert d['metric']['name'] == "foo.bar"

    def test_get_not_found(self, client, caplog):
        datapoint_id = 12
        rv = client.get(datapoint_url(datapoint_id))
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(datapoint_id) in d['detail']
        assert d['title'] == "NOT_FOUND"
        assert "API error" in caplog.text

    def test_put(self, client):
        datapoint_id = 6
        data = {
            "datapoint_id": datapoint_id,
            "metric_id": 1,
            "value": 99,
            "timestamp": 123456,
        }
        old = client.get(datapoint_url(datapoint_id)).get_json()
        rv = client.put(datapoint_url(datapoint_id), json=data)
        assert rv.status_code == 201
        new = client.get(datapoint_url(datapoint_id)).get_json()
        assert old != new
        assert old['value'] == -2
        assert new['value'] == 99

    @pytest.mark.parametrize('missing_key', ['metric_id', 'value'])
    def test_put_missing_required_key(self, client, missing_key):
        datapoint_id = 3
        data = {'metric_id': 4, 'value': 101}
        data.pop(missing_key)
        rv = client.put(datapoint_url(datapoint_id), json=data)
        assert rv.status_code == 400
        assert rv.is_json
        d = rv.get_json()
        assert missing_key in d['detail']

    @patch('trendlines.db.update_datapoint',
           MagicMock(side_effect=orm.DataPoint.DoesNotExist()))
    def test_put_datapoint_does_not_exist(self, client):
        datapoint_id = 690234234
        data = {
            "datapoint_id": datapoint_id,
            "metric_id": 1,
            "value": 99,
            "timestamp": 123456,
        }
        rv = client.put(datapoint_url(datapoint_id), json=data)
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(datapoint_id) in d['detail']

    @patch('trendlines.db.update_datapoint',
           MagicMock(side_effect=orm.Metric.DoesNotExist()))
    def test_put_metric_does_not_exist(self, client):
        datapoint_id = 6
        metric_id = 999
        data = {
            "datapoint_id": datapoint_id,
            "metric_id": metric_id,
            "value": 99,
            "timestamp": 123456,
        }
        rv = client.put(datapoint_url(datapoint_id), json=data)
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(metric_id) in d['detail']

    def test_patch(self, client):
        datapoint_id = 6
        data = {
            "value": 99,
        }
        old = client.get(datapoint_url(datapoint_id)).get_json()
        rv = client.patch(datapoint_url(datapoint_id), json=data)
        assert rv.status_code == 204
        new = client.get(datapoint_url(datapoint_id)).get_json()

        # Ensure that everything *except what as given in data* is the same.
        assert old != new
        for k, v in old.items():
            if k in data.keys():
                assert old[k] != new[k]
            else:
                assert old[k] == new[k]
        assert old['value'] == -2
        assert new['value'] == 99

    @patch('trendlines.db.update_datapoint',
           MagicMock(side_effect=orm.DataPoint.DoesNotExist()))
    def test_patch_datapoint_does_not_exist(self, client):
        datapoint_id = 9999999
        rv = client.patch(datapoint_url(datapoint_id), json={'value': 5})
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(datapoint_id) in d['detail']

    @patch('trendlines.db.update_datapoint',
           MagicMock(side_effect=orm.Metric.DoesNotExist()))
    def test_patch_metric_does_not_exist(self, client):
        datapoint_id = 3
        metric_id = 999
        rv = client.patch(datapoint_url(datapoint_id),
                          json={'metric_id': metric_id})
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(metric_id) in d['detail']

    def test_delete(self, client):
        datapoint_id = 6
        rv = client.delete(datapoint_url(datapoint_id))
        assert rv.status_code == 204

        # Verify it's actually been deleted
        after = client.get(datapoint_url(datapoint_id))
        assert after.status_code == 404

    def test_delete_not_found(self, client, caplog):
        datapoint_id = 103132
        rv = client.delete(datapoint_url(datapoint_id))
        assert rv.status_code == 404
        assert rv.is_json
        d = rv.get_json()
        assert str(datapoint_id) in d['detail']
        assert d['title'] == "NOT_FOUND"
        assert "API error" in caplog.text


def test_datapoint_get_no_data(client):
    rv = client.get(datapoint_url())
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert d['detail'] == "No data found."


def test_api_get_metric_as_json(client, populated_db, caplog):
    rv = client.get(metric_url(2))
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    print(d)
    assert d['metric_id'] == 2
    assert "API: get metric" in caplog.text


def test_api_get_metric_as_json_not_found(client, populated_db, caplog):
    metric_id = 99
    rv = client.get(metric_url(metric_id))
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert str(metric_id) in d['detail']
    assert d['title'] == "NOT_FOUND"
    assert "API error" in caplog.text


def test_api_delete_metric(client, populated_db):
    metric = 3
    rv = client.delete(metric_url(metric))
    assert rv.status_code == 204

    # Verify it's actually been deleted
    after = client.get(metric_url(metric))
    assert after.status_code == 404


def test_api_delete_metric_not_found(client, populated_db, caplog):
    metric_id = 99
    rv = client.delete(metric_url(metric_id))
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert str(metric_id) in d['detail']
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
    rv = client.post(metric_url(), json=data)
    assert rv.status_code == 201
    assert rv.is_json
    d = rv.get_json()
    assert d['name'] == metric
    assert d['lower_limit'] == lower_limit
    assert d['metric_id'] == 7


def test_api_post_metric_already_exists(client, populated_db):
    metric = "foo.bar"
    data = {"name": metric}
    rv = client.post(metric_url(), json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert "already exists" in d['detail']


def test_api_post_metric_missing_key(client, populated_db):
    data = {"units": "percent"}
    rv = client.post(metric_url(), json=data)
    assert rv.status_code == 400
    assert rv.is_json
    d = rv.get_json()
    assert "Missing required" in d['detail']


def test_api_put_metric(client, populated_db):
    metric_id = 3
    data = {
        "name": "foo.bar",
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 204
    assert rv.data == b""


def test_api_put_metric_sets_other_values_to_none(client, populated_db):
    metric_id = 6   # "with_everything"

    original = client.get(metric_url(metric_id))
    assert original.status_code == 200
    original = original.get_json()
    assert original['units'] == 'percent'
    assert original['upper_limit'] == 100.0
    assert original['lower_limit'] == 20.0

    data = {"name": "with_everything"}
    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 204

    new = client.get(metric_url(metric_id))
    assert new.status_code == 200
    new = new.get_json()

    assert new['units'] is None
    assert new['upper_limit'] is None
    assert new['lower_limit'] is None


def test_api_put_metric_not_found(client, populated_db):
    metric_id = 99
    data = {
        "name": "missing",
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert str(metric_id) in d['detail']
    assert "does not exist" in d['detail']


def test_api_put_metric_duplicate_name(client, populated_db):
    metric_id = 5
    old_name = "old_data"
    new_name = "foo.bar"
    data = {"name": new_name}
    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert old_name in d['detail']
    assert new_name in d['detail']
    assert "Unable to change metric name" in d['detail']


def test_api_put_metric_missing_name(client, populated_db):
    data = {"units": "goats"}
    rv = client.put(metric_url(3), json=data)
    assert rv.status_code == 400
    assert rv.is_json
    d = rv.get_json()
    assert "Missing required" in d['detail']


def test_api_put_metric_idempotence(client, populated_db):
    # TODO: I don't think this is the right way to test idempotence...
    metric_id = 3
    data = {
        "name": "foo.bar",
        "units": "lines",
        "upper_limit": 100,
        "lower_limit": 0,
    }
    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 204

    after_1 = client.get(metric_url(metric_id))

    rv = client.put(metric_url(metric_id), json=data)
    assert rv.status_code == 204

    after_2 = client.get(metric_url(metric_id))
    assert after_1.get_json() == after_2.get_json()


def test_api_patch_metric(client, populated_db):
    data = {"units": "pears"}
    rv = client.patch(metric_url(2), json=data)
    assert rv.status_code == 204
    assert rv.data == b""


def test_api_patch_metric_doesnt_change_other_values(client, populated_db):
    name = 6      # "with_everything"
    original = client.get(metric_url(name))
    assert original.status_code == 200
    original = original.get_json()
    assert original['units'] == 'percent'
    assert original['upper_limit'] == 100.0
    assert original['lower_limit'] == 20.0

    data = {"lower_limit": 0.2}
    rv = client.patch(metric_url(name), json=data)
    assert rv.status_code == 204

    new = client.get(metric_url(name))
    assert new.status_code == 200
    new = new.get_json()

    assert new['lower_limit'] == 0.2
    assert new['units'] == original['units']
    assert new['upper_limit'] == original['upper_limit']


def test_api_patch_metric_not_found(client, populated_db):
    metric_id = 99
    data = {"units": "pears"}
    rv = client.patch(metric_url(metric_id), json=data)
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert str(metric_id) in d['detail']
    assert "does not exist" in d['detail']


def test_api_patch_metric_duplicate_name(client, populated_db):
    new_name = "foo.bar"
    metric_id = 5
    old_name = "old_data"
    data = {"name": new_name}
    rv = client.patch(metric_url(metric_id), json=data)
    assert rv.status_code == 409
    assert rv.is_json
    d = rv.get_json()
    assert old_name in d['detail']
    assert new_name in d['detail']
    assert "Unable to change metric name" in d['detail']


def test_api_get_metrics(client, populated_db):
    rv = client.get(metric_url())
    assert rv.status_code == 200
    assert rv.is_json
    d = rv.get_json()
    assert 'count' in d.keys()
    assert 'next' in d.keys()
    assert 'prev' in d.keys()
    results = d['results']
    assert len(results) == 6
    assert "metric_id" in results[0].keys()
    assert results[0]['name'] == "empty_metric"


def test_api_get_metrics_no_data(client):
    rv = client.get(metric_url())
    assert rv.status_code == 404
    assert rv.is_json
    d = rv.get_json()
    assert "No data" in d['detail']
