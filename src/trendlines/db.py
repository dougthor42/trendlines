# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timezone

from .orm import Metric
from .orm import DataPoint
from .orm import db as _db


def add_metric(name, units=None):
    """
    Add a new metric to the database.

    Parameters
    ----------
    name : str
        The full metric name. Eg. `tphweb.master.coverage`
    units : str, optional
        List the units for this metric.

    Returns
    -------
    metric : :class:`orm.Metric` object
        The metric that was added.
    """
    metric, created = Metric.get_or_create(name=name, units=units)
    return metric


def add_data_point(metric, value, timestamp=None):
    """
    Add a new datapoint for a given metric.

    Parameters
    ----------
    metric : str
        The full metric name.
    value : numeric
        The value for this data point.
    timestamp : int, optional
        The POSIX timestamp for the data point. If ``None``, use
        the current timestamp.

    Returns
    -------
    new : :class:`orm.DataPoint` object
        An instance of the newly-created model object.
    """
    metric = Metric.get(Metric.name == metric)

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).timestamp()

    new = DataPoint.create(
        metric=metric,
        value=value,
        timestamp=timestamp,
    )
    return new


def get_data(metric):
    """
    Return all of the data for a given metric.

    Parameters
    ----------
    metric : str
        The full metric name.

    Returns
    -------
    data : :class:`peewee.ModelSelect`
        The returned data. Acts like an iterable of
        :class:`orm.DataPoint` objects
    """
    metric = Metric.get(Metric.name == metric)
    data = DataPoint.select().where(DataPoint.metric == metric.metric_id)
    return data

def get_recent_data(metric, age):
    """
    Return all data that is less than `age` seconds old.

    Parameters
    ----------
    metric : str
        The full metric name.
    age : int
        Only return data that is less than `age` seconds old.

    Returns
    -------
    data : iterable of :class:`orm.DataPoint` objects
    """
    metric = Metric.get(Metric.name == metric)
    now = datetime.now(timezone.utc).timestamp()

    data = DataPoint.select().where(
        (DataPoint.metric == metric.metric_id)
        & (DataPoint.timestamp > (now - age))
    )

    return data


def get_metrics():
    """
    Return a list of all metrics.

    Returns
    -------
    metrics : iterable of :class:`orm.Metric` objects
    """
    return Metric.select()
