# -*- coding: utf-8 -*-
"""
The general thought for the API of this module is that most queries
should just be simple wrappers around the peewee API to include things
like logging.

We allow most errors to be raised to the caller because most of the time
we need that information to determine things like which ErrorResponse
to send.
"""

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
    logger.debug("Querying metric '%s'" % name)

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


def insert_datapoint(metric, value, timestamp=None):
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


def get_datapoints():
    """
    Return a list of all datapoints.

    Returns
    -------
    datapoints : iterable of :class:`orm.DataPoint` objects
        If no data exists, an empty iterable is returned.
    """
    logger.debug("Querying list of datapoints.")
    # TODO: Should I raise DoesNotExist if there's no data?
    return DataPoint.select()


def get_datapoint(datapoint_id):
    """
    Return a single datapoint.

    Parameters
    ----------
    datapoint_id : int
        The internal ID of the datapoint to query

    Returns
    -------
    datapoint : :class:`orm.DataPoint` or None
        ``None`` if the item isn't found.
    """
    logger.debug("Querying datapoint: %s" % datapoint_id)
    return DataPoint.get_by_id(datapoint_id)


def update_datapoint(datapoint, metric=None, value=None, timestamp=None):
    """
    Update the value or timestamp (or both) of a datapoint.

    If ``metric``, ``value``, or ``timestamp`` is None, that item will not be
    updated.

    Parameters
    ----------
    datapoint : int or :class:`orm.DataPoint`
        The datapoint to update. Can be provided as an ``int`` for the
        ``datapoint_id`` or as a :class:`~orm.DataPoint` object directly.
    metric : int, optional
        The new metric_id that this datapoint should belong to.
    value : float, optional
        The new value for the datapoint.
    timestamp : int or "now", optional
        The new timestamp of the datapoint. If ``"now"``, then use the
        current datetime. This should be the POSIX timestamp integer (UTC).

    Returns
    -------
    datapoint : :class:`orm.DataPoint`
        The updated datapoint.

    Raises
    ------
    DataPoint.DoesNotExist : :class:`peewee.DoesNotExist`
        if the ``datapoint`` or ``datapoint_id`` is not found.
    Metric.DoesNotExist : :class:`peewee.DoesNotExist`
        if the ``metric`` is not found.
    """
    logger.debug("Updating datapoint: %s" % datapoint)

    # Shortcut the uncommon case where both things are None
    if all(x is None for x in (metric, value, timestamp)):
        logger.debug("No new values given. Nothing to do.")
        return

    # Make sure we're going to act on an existing object.
    try:
        if isinstance(datapoint, DataPoint):
            DataPoint.get_by_id(datapoint.datapoint_id)
        else:
            datapoint = get_datapoint(datapoint)
    except DataPoint.DoesNotExist:
        msg = "Unable to find datapoint %s. Can't update values."
        logger.warning(msg % datapoint)
        raise

    # We should only get down here if the row exists.
    if metric is not None:
        datapoint.metric = metric
    if value is not None:
        datapoint.value = value

    if timestamp is not None:
        if timestamp == "now":
            timestamp = datetime.now(timezone.utc).timestamp()

        # Convert our POSIX timestamp int to a python datetime object.
        # We need to (1) specify that the timestamp is in UTC and then
        # (2) make the timezone object naive because the DataPoint object
        # uses naive datetimes.
        new = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
        datapoint.timestamp = new

    # Note that `save()` will create the row if it doesn't exist. Even though
    # we don't want that, we can still use it because we check for existance,
    # and raise an error on DoesNotExist, in the above code. So in theory,
    # we never get down here on a object that doesn't exist. Thus `save()`
    # will not end up creating a row.
    # We want people to either (a) use the PK or (b) query the DataPoint
    # object before running this function.
    datapoint.save()

    return datapoint


def delete_datapoint(datapoint):
    """
    Delete a datapoint.

    Parameters
    ----------
    datapoint : int or :class:`orm.DataPoint`
        The datapoint to delete

    Raises
    ------
    DataPointDoesNotExist : :class:`peewee.DoesNotExist`
        if the ``datapoint`` or ``datapoint_id`` is not found.
    """
    logger.debug("Deleting datapoint: %s" % datapoint)

    if isinstance(datapoint, int):
        datapoint = get_datapoint(datapoint)

    datapoint.delete_instance()
