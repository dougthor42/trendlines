Usage
=====

TODO.

Adding Data
-----------

``Trendlines`` will accept both TCP and UDP data. TCP data is accepted by two
methods: the RESTful API via a `JSON Payload`_ and by the `Plaintext
Protocol`_. UDP data is only accepted by the `Plaintext Protocol`.


JSON Payload
^^^^^^^^^^^^

When using a JSON payload, you're actualy using the public RESTful API. With
it you have full control of almost all parts of the underlying database. You
can add metrics, delete data points, adjust values, and more.

To send in data using a JSON payload via an HTTP POST request:

.. code-block:: bash

   curl --data '{"metric": "foo.bar", "value": 52.88, "time": '${date +%s}'}' \
        --header "Content-Type: application/json" \
        --request POST \
        http://$SERVER/api/v1/data`


Plaintext Protocol
^^^^^^^^^^^^^^^^^^

The plaintext protocol allows for simple interaction. The only thing that you
can do with the plaintext protocol is add new data points.

The plaintext protocol accepts both TCP and UDP data.

If a metric does not exist, it will be created automatically.

.. code-block:: bash

   # TCP
   echo "foo.bar 52.88 `date +%s`" | nc $SERVER $PORT
   # UDP
   echo "foo.bar 52.88 `date +%s`" | nc -u -w 0 $SERVER $PORT
   # TCP, allowing the receiving server to determine the timestamp
   echo "foo.bar 52.88" | nc $SERVER $PORT
   # TCP, with a fixed timestamp
   echo "foo.bar 52.88 `date 1550775040" | nc $SERVER $PORT


The UDP string must follow the format ``"metric_name value [timestamp]"``.
This is a very similar format to `Graphite's plaintext protocol`_, so it is
easy to switch from ``trendlines`` to Graphite and back.

.. _`Graphite's plaintext protocol`: https://graphite.readthedocs.io/en/latest/feeding-carbon.html#the-plaintext-protocol


Viewing Data
------------

``Trendlines`` creates a simple set of web pages. A landing page at
``http://$SERVER`` provides a list of all known metrics. Clicking on a known
metric shows you the graph of historical data.

You can also export the data as JSON by sending an HTTP GET request:

.. code-block:: shell

   curl http://$SERVER/api/v1/data/$METRIC_NAME
