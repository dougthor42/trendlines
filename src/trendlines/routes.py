# -*- coding: utf-8 -*-

import json
from datetime import datetime
from datetime import timezone

from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request

# peewee
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from trendlines import logger
from . import db
from . import utils

pages = Blueprint('pages', __name__)
api = Blueprint('api', __name__)


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


@api.route("/api/v1/data/<metric>", methods=["GET"])
def get_data_as_json(metric):
    """
    Return data for a given metric as JSON.
    """
    logger.debug("API: get '%s'" % metric)
    try:
        raw_data = db.get_data(metric)
        units = db.get_units(metric)
    except DoesNotExist:
        http_status = 404
        detail = "The metric '{}' does not exist.".format(metric)
        resp = utils.Rfc7807ErrorResponse(
            type_="metric-not-found",
            title="Metric not found",
            status=http_status,
            detail=detail,
        )
        logger.warning("API error: %s" % detail)
        return resp.as_response(), http_status

    if len(raw_data) == 0:
        http_status = 404
        detail = "No data exists for metric '{}'.".format(metric)
        resp = utils.Rfc7807ErrorResponse(
            type_="no-data",
            title="No data for metric",
            status=http_status,
            detail=detail,
        )
        logger.warning("API error: %s" % detail)
        return resp.as_response(), http_status

    data = utils.format_data(raw_data, units)

    return jsonify(data)


@api.route("/api/v1/metric/<metric>", methods=["GET"])
def get_metric_as_json(metric):
    """
    Return metric information as JSON
    """
    logger.debug("API: get metric '%s'" % metric)

    try:
        raw_data = db.Metric.get(db.Metric.name == metric)
    except DoesNotExist:
        http_status = 404
        detail = "The metric '{}' does not exist".format(metric)
        resp = utils.Rfc7807ErrorResponse(
            type_="metric-not-found",
            title="Metric not found",
            status=http_status,
            detail=detail,
        )
        logger.warning("API error: %s" % detail)
        return resp.as_response(), http_status

    data = utils.format_metric_api_result(raw_data)

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
        http_status = 400
        detail = "Missing required key 'name'."
        resp = utils.Rfc7807ErrorResponse(
            type_="invalid-request",
            title="Missing required JSON key.",
            status=http_status,
            detail=detail,
        )
        logger.warning("API error: %s" % detail)
        return resp.as_response(), http_status

    try:
        exists = db.Metric.get(db.Metric.name == metric) is not None
        if exists:
            http_status = 409
            detail = "The metric '{}' already exists.".format(metric)
            resp = utils.Rfc7807ErrorResponse(
                type_="already-exists",
                title="Metric already exists",
                status=http_status,
                detail=detail,
            )
            logger.warning("API error: %s" % detail)
            return resp.as_response(), http_status
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
        "metric": {
            "name": new.name,
            "metric_id": new.metric_id,
            "units": new.units,
            "upper_limit": new.upper_limit,
            "lower_limit": new.lower_limit,
        }
    }
    return jsonify(body), 201


@api.route("/api/v1/metric/<metric>", methods=["DELETE"])
def delete_metric(metric):
    logger.debug("'api: DELETE '%s'" % metric)

    try:
        found = db.Metric.get(db.Metric.name == metric)
        found.delete_instance()
    except DoesNotExist:
        http_status = 404
        detail = "The metric '{}' does not exist".format(metric)
        resp = utils.Rfc7807ErrorResponse(
            type_="metric-not-found",
            title="Metric not found",
            status=http_status,
            detail=detail,
        )
        logger.warning("API error: %s" % detail)
        return resp.as_response(), http_status
    else:
        return "", 204
