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
    data = format_data(data)
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


@api.route("/api/v1/<metric>", methods=["GET"])
@api.route("/api/v1/data/<metric>", methods=["GET"])
def get_data_as_json(metric):
    """
    Return data for a given metric as JSON.
    """
    logger.debug("API: get '%s'" % metric)
    try:
        raw_data = db.get_data(metric)
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

    data = format_data(raw_data)

    return jsonify(data)


def format_data(data):
    """
    Helper function: format data for template consumption.

    Parameters
    ----------
    data : :class:`peewee.ModelSelect`
        The data as returned by :func:`db.get_data`

    Returns
    -------
    data : dict
        Dictionary of data where ``timestamp`` is an ISO 8601 string.
    """
    data = [{'timestamp': row.timestamp.isoformat(),
             'value': row.value,
             'id': row.datapoint_id,
             'n': n}
            for n, row in enumerate(data)]
    return {'rows': data}
