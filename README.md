# Trendlines

A simple, lightweight alternative to [Graphite](https://graphiteapp.org).

[![Build Status](https://travis-ci.org/dougthor42/trendlines.svg?branch=master)](https://travis-ci.org/dougthor42/trendlines)
[![Coverage Status](https://coveralls.io/repos/github/dougthor42/trendlines/badge.svg)](https://coveralls.io/github/dougthor42/trendlines)


## What is Trendlines?

**Trendlines** is a tool for *passively* collecting and displaying time-based
or sequential numeric data. Built on [Flask](http://flask.pocoo.org/),
[PeeWee](http://docs.peewee-orm.com/en/latest/), and
[Plotly](https://plot.ly/), it provides a simple interface for adding and
viewing your metrics.

It was created for a few reasons:

1. [Graphite](https://graphiteapp.org), while very awesome and powerful,
   does not provide a TCP way of sending in data - only UDP. **Trendlines**
   aims to provide both.
2. Graphite also does not allow you to view data using a simple sequential
   x-axis - it only uses time for the x-axis. Again, **Trendlines** allows you
   to use both.
3. It's always fun to start new projects.

**Trendlines** only accepts data that gets sent to it. It does not actively
seek out data like many other monitoring programs out there (Zabbix, Nagios,
Prometheus, etc.).


## What can I use it for?

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


## Installing


### Docker

The easiest way to get up and running with **Trendlines** is with Docker:

```bash
$ docker run p 5000:80 dougthor42/trendlines:latest
```

Then open a browser to `http://localhost:5000/` and you're all set. Add some data
(see below) and refresh the page.

> **Note:** Data will not persist when the container is destroyed!


### Docker Compose

> **WIP!**

If you're doing more than just playing around, you'll likely want to set up
Docker Compose. I've included an example Compose file
[here](/docker/docker-compose.yml).

Before using the example Compose file, you'll need to:

1. Make a directory to store the config file (and database file if using
   SQLite)
2. Make sure that dir is writable by docker-compose.
3. Create the configuration `trendlines.cfg` within that directory.

```bash
$ mkdir /var/www/trendlines
$ chmod -R a+w /var/www/trendlines
$ touch /var/www/trendlines/trendlines.cfg
```

Next, edit your new `trendlines.cfg` file as needed. At the very least, the
following is needed:

```python
# /var/www/trendlines/trendlines.cfg
SECRET_KEY = b"don't use the value written in this README file!"
DATABASE = "/data/internal.db"
```

You should be all set to bring Docker Compose up:

```bash
$ docker-compose -f path/to/docker-compose.yml up -d
```

Again, open up a browser to `http://localhost` and you're good to go. Add some
data as outlined below and start playing around.

**Note:** If you get an error complaining about "Error starting userland proxy:
Bind for 0.0.0.0:80: Unexpected error Permission denied", then try changing
the port in docker-compose.yml to something else. I like 5000 myself:

```yaml
ports:
  - 5000:80
```


## Usage

TODO.


### Sending Data

**Trendlines** accepts 2 forms of data entry: TCP via HTTP POST with a JSON
payload and UDP (not yet implemented).

To send in data using the HTTP POST method:

```bash
curl --data '{"metric": "foo.bar", "value": 52.88, "time": '${date +%s}'}' \
     --header "Content-Type: application/json" \
     --request POST \
     http://$SERVER/api/v1/data`
```

Or via UDP:

```bash
echo "foo.bar 52.88 `date +%s`" | nc $SERVER $PORT
```

The UDP string must follow the format `metric_name value timestamp`. This
is the same format that Graphite uses for their [plaintext
protocol](https://graphite.readthedocs.io/en/latest/feeding-carbon.html#the-plaintext-protocol),
so it is easy to switch from **Trendlines** to Graphite.


### Viewing Data

**Trendlines** creates a simple set of web pages. A landing page at
`http://$SERVER` provides a list of all known metrics. Clicking on a known
metric shows you the graph of historical data.

You can also export the data as JSON by sending an HTTP GET request:

```
curl http://$SERVER/api/v1/data/$METRIC_NAME
```
