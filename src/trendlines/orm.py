# -*- coding: utf-8 -*-
from pathlib import Path

from peewee import SqliteDatabase
from peewee import Model
from peewee import IntegerField
from peewee import FloatField
from peewee import TimestampField
from peewee import ForeignKeyField
from peewee import CharField
from peewee import OperationalError

from trendlines import logger


DB_OPTS = {
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,       # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0,
}

db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta(object):
        database = db


class DataModel(BaseModel):
    """
    Model for storing data points.

    I've kept this broken out into a separate class because there may be
    a point in the future where I want to switch to one-file-per-metric
    and having a separate DataModel class will make this easier.
    """
    pass


class InternalModel(BaseModel):
    """
    Model for internal data tables.

    *IF* we were to move to one-file-per-metric, then this model would
    hold all of the non-dynamically-generated tables.
    """
    pass


class Metric(InternalModel):
    """
    Table holding all of the Metric information.
    """

    metric_id = IntegerField(primary_key=True)
    name = CharField(max_length=120, unique=True)
    units = CharField(max_length=24, null=True)
    upper_limit = FloatField(null=True)
    lower_limit = FloatField(null=True)

    def __repr__(self):
        s = "<Metric: {id}, {name}, units={units}>"
        return s.format(id=self.metric_id, name=self.name, units=self.units)

    def __str__(self):
        return repr(self)


class DataPoint(DataModel):
    """
    Table holding all of the data points.
    """

    datapoint_id = IntegerField(primary_key=True)
    metric = ForeignKeyField(Metric, backref="datapoints",
                             on_delete="CASCADE")
    value = FloatField()
    timestamp = TimestampField(utc=True)

    def __repr__(self):
        s = "<DataPoint: {id}, {metric}, {value}, {timestamp}>"
        return s.format(id=self.datapoint_id,
                        metric=self.metric.name,
                        value=self.value,
                        timestamp=self.timestamp)

    def __str__(self):
        return repr(self)


def create_db(name):
    """
    Create the database and the tables.

    Does nothing if the tables already exist. Well, techinically it just
    connects and disconnects - ``create_tables`` is a noop.

    Parameters
    ----------
    name : str
        The name of the database, as given by ``app.config['DATABASE']``.
    """
    logger.debug("Creating database: '%s'." % name)
    db.init(name, pragmas=DB_OPTS)

    try:
        db.connect()
    except OperationalError:
        # .resolve() will fail for missing paths, and the `strit=False` arg
        # wasn't added until 3.6. Since dev environment is 3.5 I need
        # this try..except block.
        try:        # pragma: no cover
            full_path = Path(name).resolve()
        except FileNotFoundError:
            full_path = name
        logger.error("Unable to open database file '%s'" % full_path)
        raise

    tables = [
        Metric,
        DataPoint,
    ]
    db.create_tables(tables)
    db.close()
