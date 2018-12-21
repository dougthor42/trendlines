# Trendlines

A simple, lightweight alternative to [Graphite](https://graphiteapp.org).


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
     http://$SERVER/api/v1/add`
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
curl http://$SERVER/api/v1/get/$METRIC_NAME
```
