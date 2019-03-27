API
===

The RESTful API can be found [not implemented].


Philosophy
----------

The API is designed following these guidelines:

+ The HTTP Status code reflects the result of the API call.

  + Some people think that HTTP status code should reflect the result of the
    pipe (the HTTP request itself), and that's cool too. But that's not what
    this project will use.

+ API errors are returned with various ``4xx`` HTTP status codes and have a
  JSON payload that attempts to follow `RFC8707`_.
+ ``PUT`` cannot create new resources.
+ Using ``POST`` to create a resource will return the new resource.
+ ``POST`` for verbs (none exist yet) will not return anything.
+ ``PUT``, ``PATCH``, and ``DELETE`` will not return any data. It's up to
  the end user to decide if they want compare old and new values. Typically
  this might look like:

  .. code-block:: python

    import requests
    old = requests.get("/metric/2")
    requests.patch("/metric/2" json={"units": "new_units"})
    new = requests.get("/metric/2")
    # Find the differences
    diff = {"old": {}, "new": {}}
    for item in old.keys():
        diff['old'][item] = old[item]
        diff['new'][item] = new[item]

+ With a few exceptions, it's up to the end user to determine which ID
  to act on. The API is not "smart" with regards to ID-like strings.
  For example, to delete the metric named ``foo.bar``:

  .. code-block:: python

    import requests

    # You can't do this. Sorry!
    obj = requests.get("/metric/foo.bar")

    # instead you must do this (or similar):
    obj = request.get("/metric?name=foo.bar")['results'][0]
    rv = request.delete("/metric/{}".format(obj['metric_id']))
    assert rv.status_code == 204


.. _`RFC8707`: https://tools.ietf.org/html/rfc7807
