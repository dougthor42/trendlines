# -*- coding: utf-8 -*-
"""
"""
import tarfile
from collections import namedtuple
from datetime import datetime as dt
from io import BytesIO
from pathlib import Path

import freezegun
import pytest
import requests

BASE_URL = "http://localhost:5000/trendlines"
API_URL = BASE_URL + "/api/v1"


Data = namedtuple('Data', ['name', 'value', 'timestamp'])

DUMMY_DATA = [
    Data("foo.bar", 12.34, "2019-07-07 15:26:34"),
    Data("foo.bar", 12.96, "2019-07-07 15:26:35"),
    Data("foo.bar", 13.50, "2019-07-07 15:26:36"),
    Data("baz", -19, "2019-07-07 15:26:34"),
    Data("baz", -19.1, "2019-07-07 15:26:35"),
]


# I don't like that this uses the API that I'm trying to test.
# But I also don't feel like resolving that right now.
@pytest.fixture(scope="module", autouse=True)
def add_data(docker_services):
    for d in DUMMY_DATA:
        data = {
            "metric": d.name,
            "value": d.value,
            "timestamp": d.timestamp,
        }
        requests.post(API_URL + "/data", json=data)


@pytest.mark.parametrize("url", [
    BASE_URL,
    BASE_URL + "/api",
    BASE_URL + "/api/redoc",
    BASE_URL + "/plot/1",
    API_URL + "/data/1",     # route supports GET by name or ID
    API_URL + "/data/foo.bar",
    API_URL + "/metric",
    API_URL + "/metric/1",
    API_URL + "/datapoint",
    API_URL + "/datapoint/1",
])
def test_url_prefix(url):
    # Test that various routes work correctly when URL_PREFIX is
    # set and we're behind a proxy.
    rv = requests.get(url)
    assert rv.status_code == 200


def test_api_get_data():
    rv = requests.get(API_URL + "/data/foo.bar")
    assert rv.status_code == 200
    rows = rv.json()['rows']
    assert len(rows) == 3
    assert rows[0]['value'] == 12.34

    rv_by_id = requests.get(API_URL + "/data/1")
    assert rv_by_id.json() == rv.json()


def test_api_get_metric():
    rv = requests.get(API_URL + "/metric")
    assert rv.status_code == 200
    json = rv.json()
    assert set(json.keys()) == {'count', 'next', 'prev', 'results'}
    results = json['results']
    assert len(results) == 2
    assert json['count'] == len(results)
    assert results[1]['name'] == 'baz'

    rv_2 = requests.get(API_URL + "/metric/2")
    assert rv_2.json() == results[1]


def test_api_get_datapoint():
    rv = requests.get(API_URL + "/datapoint")
    assert rv.status_code == 200
    json = rv.json()
    assert set(json.keys()) == {'count', 'next', 'prev', 'results'}
    results = json['results']
    assert len(results) == 5
    assert json['count'] == len(results)
    assert results[3]['value'] == -19


@pytest.mark.skip(reason=("Need a reliable way to check that the plot has"
                          " actually been displayed. Perhaps Selenium"))
def test_plot_page():
    rv = request.get(BASE_URL + "/plot/1")
    assert rv.status_code == 200
    assert 'var metricId = "foo.bar"' in rv.text
