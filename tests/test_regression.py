# -*- coding: utf-8 -*-
"""
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from peewee import SqliteDatabase
from peewee_moves import DatabaseManager

from trendlines import routes
from trendlines import orm


@pytest.fixture
def db_0005(tmp_path):
    path = tmp_path / "foo.db"
    manager = DatabaseManager(SqliteDatabase(str(path)))
    manager.upgrade("0005")
    print(path)
    yield path
    path.unlink()


@pytest.fixture
def db_0005_with_data(db_0005):
    orm.db.init(str(db_0005), pragmas=orm.DB_OPTS)
    with orm.db:
        m1 = orm.Metric.create(name="foo")
        m2 = orm.Metric.create(name="bar")
        orm.DataPoint.create(metric=m1, value=1, timestamp=1557860569)
        orm.DataPoint.create(metric=m1, value=3, timestamp=1557860570)
        orm.DataPoint.create(metric=m1, value=5, timestamp=1557860571)
        orm.DataPoint.create(metric=m2, value=2, timestamp=1557860572)
        orm.DataPoint.create(metric=m2, value=4, timestamp=1557860573)
    yield db_0005


@pytest.fixture
def db_0006(tmp_path):
    path = tmp_path / "foo.db"
    manager = DatabaseManager(SqliteDatabase(str(path)))
    manager.upgrade("0006")
    print(path)
    yield path
    path.unlink()


@pytest.fixture
def db_0006_with_data(db_0006):
    orm.db.init(str(db_0006), pragmas=orm.DB_OPTS)
    with orm.db:
        m1 = orm.Metric.create(name="foo")
        m2 = orm.Metric.create(name="bar")
        orm.DataPoint.create(metric=m1, value=1, timestamp=1557860569)
        orm.DataPoint.create(metric=m1, value=3, timestamp=1557860570)
        orm.DataPoint.create(metric=m1, value=5, timestamp=1557860571)
        orm.DataPoint.create(metric=m2, value=2, timestamp=1557860572)
        orm.DataPoint.create(metric=m2, value=4, timestamp=1557860573)
    yield db_0006


@pytest.mark.regression
@pytest.mark.gh158
def test_migration_0005_to_0006(db_0005_with_data):
    """
    There is an issue with upgrading from migration 0005 to 0006, introduced
    in #143 / 6d6b050d4bf47d5b3cdc07fef8321c54861cfea1.

    The issue is tracked in #158. Basically the upgrade would drop the
    contents of the `datapoint` table, likely because of the `ON DELETE
    CASCADE` that was added in migration 0005.
    """
    # Verify we have data
    with orm.db:
        metric_0005 = orm.db.execute_sql('SELECT * FROM "Metric"').fetchall()
        data_0005 = orm.db.execute_sql('SELECT * FROM "Datapoint"').fetchall()
        migrations = orm.db.execute_sql(
            'SELECT * FROM "migration_history"'
        ).fetchall()

    assert len(metric_0005) != 0
    assert len(data_0005) != 0
    # Make sure we do not have migration 0006 applied.
    msg = "Migration 0006 applied when it shouldn't be."
    assert not any("0006" in m[1] for m in migrations), msg

    # Then upgrade to 0006
    # Note: we can't use manager.upgrade, as that doesn't reproduce the issue
    orm.create_db(str(db_0005_with_data))

    with orm.db:
        metric_0006 = orm.db.execute_sql('SELECT * FROM "Metric"').fetchall()
        data_0006 = orm.db.execute_sql('SELECT * FROM "Datapoint"').fetchall()
        migrations = orm.db.execute_sql(
            'SELECT * FROM "migration_history"'
        ).fetchall()

    # Ensure that migration 0006 *is* applied.
    msg = "Migration 0006 is not applied, it should be."
    assert any(["0006" in m[1] for m in migrations]), msg

    # And that data still matches.
    assert len(metric_0006) != 0
    assert metric_0006 == metric_0005
    assert len(data_0006) != 0
    assert data_0006 == data_0005


@pytest.mark.regression
@pytest.mark.gh158
def test_migration_0006_to_0005(db_0006_with_data):
    # Verify we have data
    with orm.db:
        metric_0006 = orm.db.execute_sql('SELECT * FROM "Metric"').fetchall()
        data_0006 = orm.db.execute_sql('SELECT * FROM "Datapoint"').fetchall()
        migrations = orm.db.execute_sql(
            'SELECT * FROM "migration_history"'
        ).fetchall()

    assert len(metric_0006) != 0
    assert len(data_0006) != 0
    # Make sure we have migration 0006 applied.
    msg = "Migration 0006 is not applied, it should be."
    assert any("0006" in m[1] for m in migrations), msg

    # Then downgrade to 0005. `orm.create_db` doesn't have any downgrade
    # capability, so we need to use `manager.downgrade()`
    manager = DatabaseManager(SqliteDatabase(str(db_0006_with_data)))
    manager.downgrade("0005")

    with orm.db:
        metric_0005 = orm.db.execute_sql('SELECT * FROM "Metric"').fetchall()
        data_0005 = orm.db.execute_sql('SELECT * FROM "Datapoint"').fetchall()
        migrations = orm.db.execute_sql(
            'SELECT * FROM "migration_history"'
        ).fetchall()

    # Ensure that migration 0006 *is not* applied.
    msg = "Migration 0006 applied when it shouldn't be."
    assert not any("0006" in m[1] for m in migrations), msg

    # And that data still matches.
    assert len(metric_0005) != 0
    assert metric_0005 == metric_0006
    assert len(data_0005) != 0
    assert data_0005 == data_0006
