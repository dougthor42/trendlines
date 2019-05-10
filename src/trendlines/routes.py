# -*- coding: utf-8 -*-

import json
from datetime import datetime
from datetime import timezone
from functools import partial

from marshmallow_peewee import ModelSchema
from flask import Blueprint as FlaskBlueprint
from flask import jsonify
from flask import render_template as _render_template
from flask import request
from flask.views import MethodView

from flask_rest_api import Api
from flask_rest_api import Blueprint

# peewee
from peewee import DoesNotExist
from peewee import IntegrityError
from playhouse.shortcuts import model_to_dict
from playhouse.shortcuts import update_model_from_dict

from trendlines import logger
from trendlines.__about__ import __version__
from . import db
from . import orm
from .error_responses import ErrorResponse
from . import utils

pages = FlaskBlueprint('pages', __name__)
api_class = Api()
api = Blueprint("api", __name__,
                description="All API.")
api_datapoint = Blueprint("DataPoints", __name__,
                          description="CRUD datapoint(s)")
api_metric = Blueprint("Metrics", __name__,
                       description="CRUD metric(s)")


# Make sure all pages show our version.
render_template = partial(_render_template, version=__version__)


@api_class.definition("Metrics")
class MetricSchema(ModelSchema):
    class Meta:
        model = orm.Metric


@api_class.definition("DataPoints")
class DataPointSchema(ModelSchema):
    class Meta:
        model = orm.DataPoint


@pages.route("/", methods=['GET'])
@pages.route("/plot/<metric>", methods=["GET"])
def index(metric=None):
    """
    Main page.

    Also allows direct links to a specific plot.

    Parameters
    ----------
    metric : str or int, optional
        The metric_id or metric name to plot.
    """
    metric_name = None
    if metric is not None:
        # Support both metric_id and metric_name
        try:
            metric_id = int(metric)
            metric_name = orm.Metric.get(orm.Metric.metric_id == metric_id).name
        except ValueError:
            # We couldn't parse as an int, so it's a metric name instead.
            metric_name = metric

    metric_list = db.get_metrics()
    tree_data = utils.build_jstree_data(metric_list)

    return render_template('trendlines/index.html',
                           tree_data=tree_data,
                           metric_id=metric_name)


@api.route("/api/v1/data")
class Data(MethodView):
    def post(self):
        """
        Add a new value and possibly a metric if needed.

        Expected JSON payload has the following key/value pairs::

          metric: string
          value: numeric
          time: integer or missing
        """
        data = request.get_json()
        logger.debug("Received POST /api/v1/data: {}".format(data))

        try:
            metric = data['metric']
            value = data['value']
        except KeyError:
            logger.warning("Missing JSON keys 'metric' or 'value'.")
            return "Missing required key. Required keys are:", 400

        time = data.get('time', None)

        db.add_metric(metric)
        new = db.insert_datapoint(metric, value, time)

        msg = "Added DataPoint to Metric {}\n".format(new.metric)
        logger.info("Added value %s to metric '%s'" % (value, metric))
        return msg, 201


@api.route("/api/v1/data/<metric>")
class DataByName(MethodView):
    def get(self, metric):
        """
        Return data for a given metric as JSON.

        Parameters
        ----------
        metric : str or int
            The metric name or the metric internal id (int) to get data for.
        """
        logger.debug("GET /api/v1/data/%s" % metric)

        # Support both metric_id and metric_name
        try:
            metric_id = int(metric)
            metric_name = orm.Metric.get(orm.Metric.metric_id == metric_id).name
        except ValueError:
            # We couldn't parse as an int, so it's a metric name instead.
            metric_name = metric

        try:
            raw_data = db.get_data(metric_name)
            units = db.get_units(metric_name)
        except DoesNotExist:
            return ErrorResponse.metric_not_found(metric_name)

        if len(raw_data) == 0:
            return ErrorResponse.metric_has_no_data(metric_name)

        data = utils.format_data(raw_data, units)

        return jsonify(data)


@api_datapoint.route("/api/v1/datapoint")
class DataPoint(MethodView):
    @api_datapoint.response(DataPointSchema(many=True))
    def get(self):
        """
        Return all of the data for all metrics.
        """
        logger.debug("api: GET all datapoints")
        raw_data = db.get_datapoints()
        if len(raw_data) == 0:
            # do a thing.
            return ErrorResponse.no_data()

        data = [model_to_dict(m) for m in raw_data]

        # For now, fill in dummy values.
        return jsonify({"count": len(data),
                        "prev": None,
                        "next": None,
                        "results": data})

    @api_datapoint.response(DataPointSchema, code=201)
    def post(self):
        """
        Insert a new datapoint.

        Note that this is different from the "data" route, which will
        automatically create a new metric if needed. This route will not do so.
        """
        data = request.get_json()

        # Verify all required keys exist
        required = ['metric_id', 'value']
        try:
            metric_id = data['metric_id']
            value = data['value']
        except KeyError:
            return ErrorResponse.missing_required_key(required)

        timestamp = data.get('timestamp', None)

        try:
            metric = db.Metric.get(db.Metric.metric_id == metric_id)
        except db.Metric.DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)

        new = db.insert_datapoint(metric.name, value, timestamp)

        return jsonify(model_to_dict(new)), 201


@api_datapoint.route("/api/v1/datapoint/<datapoint_id>")
class DataPointById(MethodView):

    def _put_patch(self, datapoint_id, metric_id, value, timestamp):
        """
        PUT (replace) or PATCH (update) a datapoint.

        Handles the various DoesNotExist errors that can be raised.
        """
        try:
            db.update_datapoint(datapoint_id, metric_id, value, timestamp)
        except db.DataPoint.DoesNotExist:
            return ErrorResponse.datapoint_not_found(datapoint_id)
        except db.Metric.DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)

    @api_datapoint.response(DataPointSchema)
    def get(self, datapoint_id):
        """
        Return the data for a single datapoint.
        """
        logger.debug("api: GET datapoint by ID")
        try:
            raw_data = db.get_datapoint(datapoint_id)
        except DoesNotExist:
            return ErrorResponse.datapoint_not_found(datapoint_id)

        data = model_to_dict(raw_data)
        return jsonify(data)

    @api_datapoint.response(code=201)
    def put(self, datapoint_id):
        """
        Replace a datapoint with new values.
        """
        data = request.get_json()

        # Parse our json.
        try:
            metric_id = data['metric_id']
            value = data['value']
        except KeyError:
            return ErrorResponse.missing_required_key(['metric_id', 'value'])

        timestamp = data.get('timestamp', None)

        return self._put_patch(datapoint_id, metric_id, value, timestamp)


    @api_datapoint.response(code=204)
    def patch(self, datapoint_id):
        """
        Update parts of a datapoint with new values.
        """
        data = request.get_json()

        metric_id = data.get('metric_id', None)
        value = data.get('value', None)
        timestamp = data.get('timestamp', None)

        return self._put_patch(datapoint_id, metric_id, value, timestamp)

    @api_datapoint.response(code=204)
    def delete(self, datapoint_id):
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


@api_metric.route("/api/v1/metric")
class Metric(MethodView):
    @api_metric.response(MetricSchema(many=True))
    def get(self):
        """
        Return a list of all metrics in the database.
        """
        logger.debug("api: GET all metrics")
        raw_data = db.get_metrics()
        if len(raw_data) == 0:
            # do a thing.
            return ErrorResponse.no_data()

        data = [model_to_dict(m) for m in raw_data]

        # For now, fill in dummy values.
        return jsonify({"count": len(data),
                        "prev": None,
                        "next": None,
                        "results": data})

    @api_metric.response(MetricSchema, code=201)
    def post(self):
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

        return jsonify(model_to_dict(new)), 201


@api_metric.route("/api/v1/metric/<metric_id>")
class MetricById(MethodView):
    @api_metric.response(MetricSchema)
    def get(self, metric_id):
        """
        Return metric information as JSON
        """
        logger.debug("API: get metric '%s'" % metric_id)

        try:
            raw_data = db.Metric.get(db.Metric.metric_id == metric_id)
        except DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)

        data = model_to_dict(raw_data)

        return jsonify(data)

    @api_metric.response(MetricSchema, code=204)
    def put(self, metric_id):
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
        204 :
            Success.
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
            metric = db.Metric.get(db.Metric.metric_id == metric_id)
            old = model_to_dict(metric)
        except DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)

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
        except IntegrityError:
            # Failed the unique constraint on Metric.name
            return ErrorResponse.unique_metric_name_required(old['name'], name)

        return 204

    @api_metric.response(code=204)
    def patch(self, metric_id):
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
            metric = db.Metric.get(db.Metric.metric_id == metric_id)
            old = model_to_dict(metric)
        except DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)

        metric = update_model_from_dict(metric, data)

        try:
            metric.save()
        except IntegrityError:
            # Failed the unique constraint on Metric.name
            return ErrorResponse.unique_metric_name_required(old['name'], metric.name)

        return 204

    @api_metric.response(code=204)
    def delete(self, metric_id):
        logger.debug("'api: DELETE '%s'" % metric_id)

        try:
            found = db.Metric.get(db.Metric.metric_id == metric_id)
            found.delete_instance()
        except DoesNotExist:
            return ErrorResponse.metric_not_found(metric_id)
