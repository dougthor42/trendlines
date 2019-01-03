# -*- coding: utf-8 -*-
"""
"""
import pytest

from trendlines import orm


def test_metric_str():
    m = orm.Metric(name="foo", units="bar")
    assert str(m) == "<Metric: None, foo, units=bar>"


def test_datapoint_str():
    m = orm.Metric(name="foo")
    d = orm.DataPoint(metric=m, value=15.34, timestamp=10)
    assert str(d) == "<DataPoint: None, foo, 15.34, 10>"
