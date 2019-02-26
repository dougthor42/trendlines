# -*- coding: utf-8 -*-

import json
from datetime import datetime
from datetime import timezone
from functools import partial

from flask import Blueprint
from flask import jsonify
from flask import render_template as _render_template
from flask import request

# peewee
from peewee import DoesNotExist
from peewee import IntegrityError
from playhouse.shortcuts import model_to_dict
from playhouse.shortcuts import update_model_from_dict

from trendlines import logger
from trendlines.__about__ import __version__
from . import db
from .error_responses import ErrorResponse
from . import utils

pages = Blueprint('pages', __name__)
api = Blueprint('api', __name__)


# Make sure all pages show our version.
render_template = partial(_render_template, version=__version__)


@pages.route('/', methods=['GET'])
def index():
    """
    Main page.

    Displays a list of all the known metrics with links.
    """
    raw_data = db.get_metrics()
    data = utils.build_jstree_data(m.name for m in raw_data)
    return render_template("trendlines/index.html", data=data)


@pages.route("/plot/<metric>", methods=["GET"])
def plot(metric=None):
    """
    Plot a given metric.
    """
    if metric is None:
        return "Need a metric, friend!"

    data = db.get_data(metric)
    units = db.get_units(metric)
    data = utils.format_data(data, units)
    if len(data) == 0:
        logger.warning("No data exists for metric '%s'" % metric)
        return "Metric '{}' wasn't found. No data, maybe?".format(metric)

    # TODO: Ajax request for this data instead of sending it to the template.
    return render_template('trendlines/plot.html', name=metric, data=data)


@api.route("/api/v1/data", methods=['POST'])
def post_datapoint():
    """
    Add a new value and possibly a metric if needed.

    Expected JSON payload has the following key/value pairs::

      metric: string
      value: numeric
      time: integer or missing
    """
    data = request.get_json()

    try:
        metric = data['metric']
        value = data['value']
    except KeyError:
        logger.warning("Missing JSON keys 'metric' or 'value'.")
        return "Missing required key. Required keys are:", 400

    time = data.get('time', None)

    db.add_metric(metric)
    new = db.add_data_point(metric, value, time)

    msg = "Added DataPoint to Metric {}\n".format(new.metric)
    logger.info("Added value %s to metric '%s'" % (value, metric))
    return msg, 201


@api.route("/api/v1/data/<metric_name>", methods=["GET"])
def get_data_as_json(metric_name):
    """
    Return data for a given metric as JSON.
    """
    logger.debug("API: get '%s'" % metric_name)
    try:
        raw_data = db.get_data(metric_name)
        units = db.get_units(metric_name)
    except DoesNotExist:
        return ErrorResponse.metric_not_found(metric_name)

    if len(raw_data) == 0:
        return ErrorResponse.metric_has_no_data(metric_name)

    data = utils.format_data(raw_data, units)

    return jsonify(data)


@api.route("/api/v1/datapoint", methods=["GET"])
def api_get_all_datapoints():
    """
    Return all of the data for all metrics.
    """
    pass


@api.route("/api/v1/datapoint", methods=["POST"])
def api_post_datapoint():
    """
    Insert a new datapoint.

    Note that this is different from the "data" route, which will
    automatically create a new metric if needed. This route will not do so.
    """
    pass


@api.route("/api/v1/datapoint/<datapoint_id>", methods=["GET"])
def api_get_datapoint(datapoint_id):
    """
    Return the data for a single datapoint.
    """
    pass


@api.route("/api/v1/datapoint/<datapoint_id>", methods=["PUT"])
def apit_put_datapoint(datapoint_id):
    """
    Replace a datapoint with new values.
    """
    pass


@api.route("/api/v1/datapoint/<datapoint_id>", methods=["PATCH"])
def api_patch_datapoint(datapoint_id):
    """
    Update parts of a datapoint with new values.
    """
    pass


@api.route("/api/v1/datapoint/<datapoint_id>", methods=["DELETE"])
def api_delete_datapoint(datapoint_id):
    """
    Delete a datapoint.
    """
    logger.debug("'api: DELETE datapoint '%s'" % datapoint_id)

    try:
        found = db.DataPoint.get(db.DataPoint.datapoint_id == datapoint_id)
        found.delete_instance()
    except DoesNotExist:
        return ErrorResponse.datapoint_not_found(datapoint_id)
    else:
        return "", 204


@api.route("/api/v1/metric", methods=["GET"])
def api_get_metrics():
    """
    Return a list of all metrics in the database.
    """
    pass


@api.route("/api/v1/metric/<metric_name>", methods=["GET"])
def get_metric_as_json(metric_name):
    """
    Return metric information as JSON
    """
    logger.debug("API: get metric '%s'" % metric_name)

    try:
        raw_data = db.Metric.get(db.Metric.name == metric_name)
    except DoesNotExist:
        return ErrorResponse.metric_not_found(metric_name)

    data = model_to_dict(raw_data)

    return jsonify(data)


@api.route("/api/v1/metric", methods=["POST"])
def post_metric():
    """
    Create a new metric.

    Accepts JSON data with the following format:

    .. code-block::json
       {
         "name": "your.metric_name.here",
         "units": string, optional,
         "upper_limit": {float, optional},
         "lower_limit": {float, optional},
       }

    Returns ``201`` on success, ``400`` on malformed JSON data (such as when
    ``name`` is missing), or ``409`` if the metric already exists.

    See Also
    --------
    :func:`routes.get_metric_as_json`
    :func:`routes.delete_metric`
    """
    data = request.get_json()

    try:
        metric = data['name']
    except KeyError:
        return ErrorResponse.missing_required_key('name')

    try:
        exists = db.Metric.get(db.Metric.name == metric) is not None
        if exists:
            return ErrorResponse.metric_already_exists(metric)
    except DoesNotExist:
        logger.debug("Metric does not exist. Able to create.")

    units = data.get('units', None)
    lower_limit = data.get('lower_limit', None)
    upper_limit = data.get('upper_limit', None)

    new = db.add_metric(metric, units=units, lower_limit=lower_limit,
                        upper_limit=upper_limit)

    # Our `db.add_metric` fuction doesn't pull the new metric_id, so we
    # grab that separately.
    new.metric_id = db.Metric.get(db.Metric.name == new.name).metric_id

    msg = "Added Metric '{}'".format(metric)
    body = {
        "message": msg,
        "metric": model_to_dict(new)
    }
    return jsonify(body), 201


@api.route("/api/v1/metric/<metric_name>", methods=["DELETE"])
def delete_metric(metric_name):
    logger.debug("'api: DELETE '%s'" % metric_name)

    try:
        found = db.Metric.get(db.Metric.name == metric_name)
        found.delete_instance()
    except DoesNotExist:
        return ErrorResponse.metric_not_found(metric_name)
    else:
        return "", 204


@api.route("/api/v1/metric/<metric_name>", methods=["PUT"])
def put_metric(metric_name):
    """
    Replace a metric with new values.

    This function cannot change the ``metric_id`` value.

    Keys not given are assumed to be ``None``.

    Accepts JSON data with the following format:

    .. code-block::json
       {
         "name": "your.metric_name.here",
         "units": {string, optional},
         "upper_limit": {float, optional},
         "lower_limit": {float, optional},
       }

    Returns
    -------
    200 :
        Success. Returned JSON data has two keys: ``old_value`` and
        ``new_value``, each containing a full :class:`orm.Metric` object.
    400 :
        Malformed JSON data (such as when ``name`` is missing)
    404 :
        The requested metric is not found.
    409 :
        The metric already exists.


    See Also
    --------
    :func:`routes.get_metric_as_json`
    :func:`routes.post_metric`
    :func:`routes.delete_metric`
    """
    data = request.get_json()

    # First see if our item actually exists
    try:
        metric = db.Metric.get(db.Metric.name == metric_name)
        old = model_to_dict(metric)
    except DoesNotExist:
        return ErrorResponse.metric_not_found(metric_name)

    # Parse our json.
    try:
        name = data['name']
    except KeyError:
        return ErrorResponse.missing_required_key('name')

    # Update fields with new values, assuming None if missing.
    for k in old.keys():
        setattr(metric, k, data.get(k, None))

    # We need to manually set the primary key because our little setattr
    # hack above doesn't seem to work. We need to set the PK in general so
    # that peewee's `save` method performs an UPDATE instead of INSERT.
    metric.metric_id = old['metric_id']

    try:
        metric.save()
        new = model_to_dict(metric)
    except IntegrityError:
        # Failed the unique constraint on Metric.name
        return ErrorResponse.unique_metric_name_required(old['name'], name)

    rv = {"old_value": old, "new_value": new}

    return jsonify(rv), 200


@api.route("/api/v1/metric/<metric_name>", methods=["PATCH"])
def patch_metric(metric_name):
    """
    Update the values for a given metric.

    This cannot change the ``metric_id`` value.

    Accepts JSON data with the following format:

    .. code-block::json
       {
         "name": {string, optional},
         "units": {string, optional},
         "upper_limit": {float, optional},
         "lower_limit": {float, optional}
       }

    Returns
    -------
    200 :
        Success. Returned JSON data has two keys: ``old_value`` and
        ``new_value``, each containing only the values of the
        :class:`orm.Metric` object *that were requested to be changed*.
    404 :
        The requested metric is not found.
    409 :
        The target metric name already exists.

    See Also
    --------
    :func:`routes.get_metric_as_json`
    :func:`routes.post_metric`
    :func:`routes.delete_metric`
    :func:`routes.put_metric`
    """
    # XXX: This is essentially the same code as `put`... Gotta refactor ASAP
    data = request.get_json()

    # First see if our item actually exists
    try:
        metric = db.Metric.get(db.Metric.name == metric_name)
        old = model_to_dict(metric)
    except DoesNotExist:
        return ErrorResponse.metric_not_found(metric_name)

    metric = update_model_from_dict(metric, data)

    try:
        metric.save()
    except IntegrityError:
        # Failed the unique constraint on Metric.name
        return ErrorResponse.unique_metric_name_required(old['name'], metric.name)

    new = model_to_dict(metric)

    # Only return the values that were requested to be changed (even if they
    # did not change).
    # This seems like a silly way to do it. Is there a better way?
    rv = {'old_value': {}, 'new_value': {}}
    for item in data.keys():
        rv['old_value'][item] = old[item]
        rv['new_value'][item] = new[item]

    return jsonify(rv), 200
