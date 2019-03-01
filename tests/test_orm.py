# -*- coding: utf-8 -*-
"""
"""
import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from peewee import OperationalError
from peewee import SqliteDatabase
from peewee_moves import DatabaseManager

from trendlines import orm


def _hash_file(path, algorithm=hashlib.md5):
    """
    Return the hash of a file. Not very efficient but I don't care.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        The path to the file to hash.
    method : function, optional
        One of the ``hashlib`` algorithms. Defaults to ``hashlib.md5``

    Returns
    -------
    str
        The hex representation of the hash.
    """
    return algorithm(open(str(path), 'rb').read()).hexdigest()


@pytest.fixture
def up_to_date_db(tmp_path):
    """
    Return a database that has all migrations applied.
    """
    path = tmp_path / "foo.db"
    manager = DatabaseManager(SqliteDatabase(str(path)))
    manager.upgrade()
    yield path
    path.unlink()


@pytest.fixture
def outdated_db(up_to_date_db):
    """
    Return a database file that is missing some migrations.
    """
    # Rename things to avoid confusion
    path = up_to_date_db
    # Start with an up-to-date database, then downgrade
    manager = DatabaseManager(SqliteDatabase(str(path)))
    manager.downgrade()
    yield path


@pytest.fixture
def broken_db(outdated_db):
    """
    Return a database file that is broken and cannot have migrations applied.
    """
    path = outdated_db
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
    c.execute('DROP TABLE datapoint;')
    conn.commit()
    conn.close()
    yield path


def test_metric_str():
    m = orm.Metric(name="foo", units="bar")
    assert str(m) == "<Metric: None, foo, units=bar>"


def test_datapoint_str():
    m = orm.Metric(name="foo")
    d = orm.DataPoint(metric=m, value=15.34, timestamp=10)
    assert str(d) == "<DataPoint: None, foo, 15.34, 10>"


def test_create_db(tmp_path):
    path = tmp_path / "foo.db"
    orm.create_db(str(path))
    # if the function worked the file should now exist.
    assert path.exists()


@patch("trendlines.orm.db.connect", MagicMock(side_effect=OperationalError))
def test_create_db_logs_and_raises_operational_error(caplog):
    with pytest.raises(OperationalError):
        orm.create_db("foo")

    assert "Unable to create/open database file" in caplog.text
    assert "foo" in caplog.text


def test_create_db_new_file(tmp_path, caplog):
    path = tmp_path / "foo.db"
    orm.create_db(str(path))
    # if the function worked the file should now exist.
    assert path.exists()
    assert "Missing migrations:" in caplog.text
    # for new files, all migrations should be missing. If the 1st is missing,
    # that implies that the rest are missing as well.
    assert "0001" in caplog.text


def test_create_db_nothing_to_do(up_to_date_db, caplog):
    orm.create_db(str(up_to_date_db))
    assert "Database is up to date." in caplog.text


def test_create_db_applies_missing_migrations(outdated_db, caplog):
    orm.create_db(str(outdated_db))
    assert "Missing migrations:" in caplog.text
    assert "Created database backup" in caplog.text
    assert "Successfully applied database migrations" in caplog.text


@freeze_time("2019-02-28 15:02:02")
def test_create_db_failure(broken_db, caplog):
    # orm.db.init changes the file so we can't look at a "before" hash.

    # Run the migration (will fail)
    orm.create_db(str(broken_db))

    # Make sure our original file and backup files exist, and are the same
    backup_file = Path("{}.{}".format(str(broken_db), "20190228_150202"))
    assert broken_db.exists()
    assert backup_file.exists()
    assert _hash_file(broken_db) == _hash_file(backup_file)

    # and lastly check our logs.
    assert "Missing migrations:" in caplog.text
    assert "Created database backup" in caplog.text
    assert "Failed to apply database migrations" in caplog.text
    assert "Reverting to backup file" in caplog.text


@patch("trendlines.orm.db.connect", MagicMock(side_effect=OperationalError))
def test_create_db_operational_error_and_file_exists(up_to_date_db, caplog):
    with pytest.raises(OperationalError):
        orm.create_db(str(up_to_date_db))

    assert "but we're unable to connect" in caplog.text


@patch("peewee_moves.DatabaseManager.upgrade", MagicMock(return_value=False))
def test_create_db_migration_failure_on_new_file(tmp_path, caplog):
    orm.create_db(str(tmp_path / "foo.db"))
    expected = "Failed to apply database migrations to the new file"
    assert expected in caplog.text


@patch("trendlines.orm.DatabaseManager",
    MagicMock(side_effect=PermissionError)
)
def test_create_db_run_migrations_in_docker_fails(outdated_db, caplog):
    with pytest.raises(PermissionError):
        orm.create_db(str(outdated_db))
    assert "Failed to open default migration directory" in caplog.text
    assert "Success" not in caplog.text
    assert "Successfully applied database migrations" not in caplog.text


def _fake_db_manager():
    """
    Needed by ``test_create_db_run_migrtations_in_docker``.

    Because of poor design choices, we call
    :class:`peewee_moves.DatabaseManager` twice within
    :func:`orm.create_db`. We need to have the first call
    raise ``PermissionError`` and the second return a correct
    :class:~`peewee_moves.DatabaseManager` object.

    Having the mocked object return two different values is pretty easy:
    simply set your ``side_effect`` to be an iterable.

    I was unable to figure out how to get the 2nd one to work. I thought
    that using :attr:`unittest.mark.DEFAULT` would work, but the issue
    there is that ``manager.diff`` would return something that resulted
    in ``needs_migrations`` being ``False``. We need that to be ``True``.

    So I decided to just mock the whole 2nd ``side_effect``.
    """
    db_manager = MagicMock()
    db_manager.diff = ["0005"]
    db_manager.upgrade = MagicMock(return_value=True)
    return db_manager


@patch("trendlines.orm.DatabaseManager",
    MagicMock(side_effect=[PermissionError, _fake_db_manager()])
)
def test_create_db_run_migrations_in_docker(outdated_db, caplog):
    orm.create_db(str(outdated_db))
    assert "Failed to open default migration directory" in caplog.text
    assert "Success" in caplog.text
    assert "Successfully applied database migrations" in caplog.text
