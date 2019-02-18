# -*- coding: utf-8 -*-

from peewee import SqliteDatabase
from peewee import Model
from peewee import IntegerField
from peewee import FloatField
from peewee import TimestampField
from peewee import ForeignKeyField
from peewee import CharField


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
