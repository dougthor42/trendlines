# -*- coding: utf-8 -*-
import shutil
from datetime import datetime
from pathlib import Path

from peewee import SqliteDatabase
from peewee import Model
from peewee import IntegerField
from peewee import FloatField
from peewee import TimestampField
from peewee import ForeignKeyField
from peewee import CharField
from peewee import OperationalError
from peewee_moves import DatabaseManager
from playhouse.sqlite_ext import AutoIncrementField

from trendlines import logger
from trendlines import utils
from trendlines.__about__ import __project_url__


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

    metric_id = AutoIncrementField()
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

    The ``timestamp`` field stores values as UTC but queries return
    naive :class:`datetime.datetime` objects (no timezone info).
    """

    datapoint_id = AutoIncrementField()
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

    Applies any missing migrations. Does nothing if all migrations
    have been applied.

    Parameters
    ----------
    name : str
        The name/path of the database, as given by ``app.config['DATABASE']``.
    """
    #  import pdb; pdb.set_trace()
    # Convert to a Path object because I like working with those better.
    full_path = Path(name).resolve()

    file_exists = full_path.exists()
    if file_exists:
        logger.debug("Connecting to existing database: '%s'." % full_path)
    else:
        logger.debug("Creating new database: '%s'" % full_path)

    db.init(str(full_path), pragmas=DB_OPTS)

    try:
        # This will create the file if it doesn't exist.
        db.connect()
    except OperationalError:
        # Try to figure out why OperationalError happened.
        if file_exists:
            msg = ("Database file %s exists, but we're unable to connect."
                   " Perhaps the permissions are incorrect?")
            logger.error(msg % full_path)
        else:
            msg = ("Unable to create %s. Perhaps the parent folder is missing"
                   " or permissions are incorrect?")
            logger.error(msg % full_path)
        logger.error("Unable to create/open database file '%s'" % full_path)
        raise

    # Either way, we want to run migrations. However, we only need to make a
    # backup if the file already exists.
    if file_exists:
        # Create a backup before doing anything.
        backup_file = utils.backup_file(full_path)
        logger.debug("Created database backup file: {}".format(backup_file))

    # This will edit the database file, creating the `migration_history`
    # table if needed. Hence why we do it *after* the backup.
    try:
        manager = DatabaseManager(db)
    except PermissionError:
        # When runnng in the docker container, this will attempt to create
        # a `/migrations` directory. It should be `/trendlines/migrations`.
        # If this still fails, let the error propogate but make sure to
        # close the db connection
        try:
            msg = "Failed to open default migration directory, trying '%s'"
            alt_dir = "/trendlines/migrations"
            logger.debug(msg % alt_dir)
            manager = DatabaseManager(db, directory=alt_dir)
            logger.debug("Success")
        except PermissionError:
            raise
        finally:
            db.close()

    # Check the status. Creating a new file means we'll need migrations.
    # However, we don't need to check for that because it's guaranteed
    # that a new file will have len(manager.diff) > 0
    needs_migrations = len(manager.diff) > 0

    if needs_migrations:
        logger.info("Missing migrations: {}".format(manager.diff))

        # Apply the migrations
        success = manager.upgrade()
        if success:
            logger.info("Successfully applied database migrations.")
        elif file_exists:
            # revert our changes by restoring the backup
            msg = ("Failed to apply database migrations. Reverting to backup"
                   " file. Please submit an issue at {} with details.")
            logger.critical(msg.format(__project_url__))
            shutil.copy(str(backup_file), str(full_path))
        else:
            # It's a new file, so no backup was made.
            msg = ("Failed to apply database migrations to the new file."
                   " Please see the logs for more info.")
            logger.critical(msg)
    else:
        logger.info("Database is up to date. No migrations to apply.")
        # Since we didn't make any changes, we can remove the backup file.
        # Is it possible to ever have backup_file not exist if we didn't
        # apply migrations?
        # No, because not applying migrations implies that the file already
        # existed, and if the file already existed then a backup was made.
        # Thus we don't need to check for FileNotFoundError.
        backup_file.unlink()
        logger.debug("Removed superfluous backup file: %s" % backup_file)

    # Make sure to close the database if things went well.
    db.close()
