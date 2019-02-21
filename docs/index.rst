.. Trendlines documentation master file, created by
   sphinx-quickstart on Thu Feb 21 09:37:36 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Trendlines's documentation!
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   upgrading
   usage
   api
   development
   modules/trendlines


What is Trendlines?
-------------------

``Trendlines`` is a tool for *passively* collecting and displaying time-based
or sequential numeric data. Built on Flask_, Peewee_, and Plotly_, it
provides a simple interface for adding and viewing your metrics.

.. _flask: http://flask.pocoo.org/
.. _peewee: http://docs.peewee-orm.com/en/latest/
.. _plotly: https://plot.ly/

It was created for a few reasons:

1. Graphite_, while very awesome and powerful, does not provide a RESTful API
   for adding and retrieving data. (To my knowledge. Please correct me if I'm
   wrong). ``Trendlines`` aims to provide both the RESTful API and the
   plaintext protocol.
2. Graphite also does not allow you to view data using a simple sequential
   x-axis - it only uses time for the x-axis. Again, ``Trendlines`` allows you
   to use both.
3. It's always fun to start new projects.

.. _graphite: https://graphiteapp.org

``Trendlines`` only accepts data that gets sent to it. It does not actively
seek out data like many other awesome monitoring programs out there (Zabbix_,
Nagios_, Prometheus_, etc.).

.. _zabbix: https://www.zabbix.com/
.. _nagios: https://www.nagios.org/
.. _prometheus: https://prometheus.io/


What can I use it for?
----------------------

Anything, really. Well, anything that (a) you can assign a number to and
(b) might change over time.

Examples include:

+ Test coverage per project
+ Code quality metrics per commit
+ House temperature
+ Distance driven per trip
+ Distance per fillup (or per charge for the eco-friendly folk)
+ How many times the dog barks
+ How often some clicks the Big Red Button on your webpage

It's been designed to handle infrequent, variable interval data. Sometimes
real-world data just doesn't appear at nice, regular intervals.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
