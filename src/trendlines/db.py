# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timezone

from trendlines import logger
from .orm import Metric
from .orm import DataPoint
from .orm import db as _db


def add_metric(name, units=None, lower_limit=None, upper_limit=None):
    """
    Add a new metric to the database.

    If both ``lower_limit`` and ``upper_limit`` are given, then
    ``upper_limit`` must be greater than ``lower_limit``.

    Parameters
    ----------
    name : str
        The full metric name. Eg. `tphweb.master.coverage`
    units : str, optional
        List the units for this metric.
    lower_limit: float, optional
        The lower limit for data. Data values below this limit will trigger
        email alerts.
    upper_limit: float, optional
        The upper limit for data. Data values above this limit will trigger
        email alerts.

    Returns
    -------
    metric : :class:`orm.Metric` object
        The metric that was added.

    Raises
    ------
    ValueError
        The provide limits do not satisfy ``upper_limit <= lower_limit``.
    TypeError
        The provided limits are not numeric or ``None``.
    """
    logger.debug("Querying metric %s" % name)

    _t = (int, float, type(None))
    if not isinstance(lower_limit, _t) or not isinstance(upper_limit, _t):
        msg = "Invalid type for limits. lower_limit: {}. upper_limit: {}"
        logger.error(msg.format(type(lower_limit), type(upper_limit)))
        raise TypeError("upper_limit and lower_limit must be numerics or None.")

    if lower_limit is not None and upper_limit is not None:
        if upper_limit <= lower_limit:
            logger.error("upper_limit not greater than lower_limit.")
            raise ValueError("upper_limit must be greater than lower_limit")

    metric, created = Metric.get_or_create(
        name=name,
        units=units,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
    )
    if created:
        logger.info("Metric '%s' created." % name)
    else:
        logger.debug("Found existing metric '%s'." % name)
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
    logger.debug("Adding data point %s to metric '%s'" % (value, metric))
    metric = Metric.get(Metric.name == metric)

    if timestamp is None:
        logger.debug("Timestamp not given, using current time.")
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
    logger.debug("Querying data for '%s'" % metric)
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
    logger.debug("Querying last %s seconds of data for '%s'." % (age, metric))
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
    logger.debug("Querying list of metrics.")
    return Metric.select()


def get_units(metric):
    """
    Return the units for a given metric.

    Parameters
    ----------
    metric : str

    Returns
    -------
    units : str
    """
    units = Metric.get(Metric.name == metric).units
    return units
