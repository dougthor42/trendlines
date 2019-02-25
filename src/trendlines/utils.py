# -*- coding: utf-8 -*-
"""
"""
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone

from flask import current_app
from flask import jsonify
from flask import url_for


@contextmanager
def adjust_jsonify_mimetype(new_type):
    """
    Context Manager. Temporarily adjust the application's JSONIFY_MIMETYPE.

    Must be run within an application context, as it uses ``current_app``.

    Parameters
    ----------
    new_type : str
        The new Content-Type / Mimetype to use during ``jsonify``.
    """
    var_name = 'JSONIFY_MIMETYPE'
    old = current_app.config[var_name]
    current_app.config[var_name] = new_type
    yield
    current_app.config[var_name] = old


def get_metric_parent(metric):
    """
    Determine the parent of a metric.

    If no parent exists, the root ``#`` is given.

    Parameters
    ----------
    metric : str
        The dotted metric to act on.

    Returns
    -------
    parent : str

    Examples
    --------
    >>> get_metric_parent("foo")
    "#"
    >>> get_metric_parent("foo.bar")
    "foo"
    >>> get_metric_parent("foo.bar.baz.foo")
    "foo.bar.baz"
    """
    s = metric.split(".")
    if len(s) == 1:
        # top-level item. parent is "#" (root)
        parent = "#"
    else:
        parent = ".".join(s[:-1])

    return parent


def format_metric_for_jstree(metric):
    """
    Format a metric name into a dict consumable by jsTree.

    See "Alternative JSON format" in the `jsTree docs`_.

    .. _`jsTree docs`: https://www.jstree.com/docs/json/

    Parameters
    ----------
    metric : str
        The metric name to format.

    Returns
    -------
    dict
        A dict with the following keys: id, parent, text, url
    """
    parent = get_metric_parent(metric)
    url = url_for('pages.plot', metric=metric)
    return {"id": metric, "parent": parent, "text": metric, "url": url}


def build_jstree_data(metrics):
    """
    Build a list of dicts consumable by jsTree.

    Fills in missing parent nodes.

    Parameters
    ----------
    metrics : list of str
        The metric names to display. Note that this is *not* the Metric
        objects themselves, but rather a simple list of strings (metric
        names). Take the results of :func:`db.get_metrics`::

           raw_data = db.get_metrics()
           tree = build_jstree_data(m.name for m in raw_data)

    Returns
    -------
    data : list of dict
        A JSON-serializable list of dicts. Each dict has at least ``id`` and
        ``parent`` keys. If the metric doesn't exist (it's just a placeholder
        parent), then the value of the ``url`` key will be ``None``.

    Notes
    -----
    Given the following metrics::

        foo
        foo.bar
        bar.baz.biz

    The return value of this function will be:

    .. code-block:: python

       # Spacing added for readability
       # The `text` key is removed for readabiity.
       [
        {"id": "foo",         "parent": "#",       "url": "/plot/foo"         },
        {"id": "foo.bar",     "parent": "foo",     "url": "/plot/foo.bar"     },
        {"id": "bar",         "parent": "#",       "url": None                },
        {"id": "bar.baz",     "parent": "bar",     "url": None                },
        {"id": "bar.baz.biz", "parent": "bar.baz", "url": "/plot/bar.baz.biz" },
       ]
    """
    # First go through and make all of our existing links
    data = [format_metric_for_jstree(m) for m in metrics]

    # then search through that data and find any missing parents.
    for m in data:
        parent = m["parent"]

        # ignore root nodes and parents that already exist.
        if parent == "#" or parent in (x['id'] for x in data):
            continue

        # Create the grandparent
        new_parent = get_metric_parent(parent)

        # Add the new, non-linked item to our data. Yes we're intentionally
        # modifying the array we're looping over so that we make sure to
        # get all parents no matter how deep.
        new = {"id": m['parent'],
               "parent": new_parent,
               "text": m['parent'],
               "url": None,
               }
        data.append(new)

    # Lastly sort things in a predictable fashion.
    data.sort(key=lambda d: d['id'])
    return data


def format_data(data, units=None):
    """
    Helper function: format data for template consumption.

    Parameters
    ----------
    data : :class:`peewee.ModelSelect`
        The data as returned by :func:`db.get_data`

    units : str, optional
        The units of the data, if any. The :meth:`db.get_units` function can
        be used to get this value.

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
    return {'rows': data, "units": units}


def parse_socket_data(data):
    """
    Parse socket data to a dict suitable for sending to ``/api/v1/data``.

    Parameters
    ----------
    data : str
        The raw string sent in via a TCP or UDP socket. This should follow
        the "metric value [timestamp]" format. If ``timestamp`` is not given,
        then the time that the request was received will be used.

    Returns
    -------
    dict
        A dict suitable for sending via :module:`requests` as JSON.
    """
    try:
        data = data.decode("utf-8")
    except AttributeError:
        # 'data' is already a string, not bytes.
        pass

    s = data.split(" ")
    try:
        metric, value = s[0], float(s[1])
    except Exception:
        raise ValueError("Failed to parse `%s` % data")

    try:
        time = int(s[2])
    except IndexError:
        time = int(datetime.now(timezone.utc).timestamp())

    d = {"metric": metric, "value": value, "time": time}

    return d
