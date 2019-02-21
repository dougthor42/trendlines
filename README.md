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

## Quickstart

Install and run in a development environment using Docker:

```bash
docker run -p 5000:80 -d dougthor42/trendlines:latest
```

Send in some data:

> **Note:** there are simplier ways to do this. Please see the
[usage documentation](https://trendlines.readthedocs.io/en/latest/usage.html)
for details.

```bash
curl -X POST --data '{"metric": "my.metric", "value": 12.234}" \
     --header "Content-Type: application/json" \
     http://localhost:5000/api/v1/data
```

And then open up a browser and navigate to `http://localhost:5000`.

## Documentation

Full documentation is hosted by ReadTheDocs. It can be found
[here](https://trendlines.readthedocs.io/en/latest/).
