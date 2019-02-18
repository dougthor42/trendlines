"""
on_delete_cascade_metric
date created: 2019-02-18 20:14:29.517083
"""

def _alter_constraint(migrator, new):
    """
    Alter the constraint for a table.

    This is definitely not an optimal solution, but we need it because:
    1.  SQLite doesn't support DROP CONSTRAINT, so we need to make a new
        table with the proper constraints and then copy all the data over.
    2.  When we try to make a new table with peewee-moves, the constraint
        name is the same as an existing table. So we need to delete that
        existing table first. We don't want to lose that data, so we put it
        into an intermediate table.

    Parameters
    ----------
    migrator :
        The migrator object.
    new : dict
        The new foreign key parameters
    """
    # Create an intermediate table with no FKs or constraints
    with migrator.create_table('intermediate') as table:
        table.int('datapoint_id')
        table.int('metric_id')
        table.float('value')
        table.int('timestamp')

    # Copy all of our data over to this intermediate table.
    sql = "INSERT INTO 'intermediate' SELECT * FROM datapoint;"
    cursor = migrator.execute_sql(sql)

    # Drop our original table
    migrator.drop_table('datapoint')

    # Create the original table with the new FK constraints.
    with migrator.create_table('datapoint') as table:
        table.int('datapoint_id', primary_key=True)
        table.foreign_key(**new)
        table.float('value')
        table.int('timestamp')

    # Copy everything from the intermediate location to the new table.
    sql = "INSERT INTO 'datapoint' SELECT * FROM 'intermediate';"
    cursor = migrator.execute_sql(sql)

    migrator.drop_table('intermediate')


def upgrade(migrator):
    new = {
        'coltype': 'INT',
        'name': 'metric_id',
        'references': 'metric.metric_id',
        'on_delete': 'CASCADE',
        'on_update': None,
    }

    _alter_constraint(migrator, new)


def downgrade(migrator):
    new = {
        'coltype': 'INT',
        'name': 'metric_id',
        'references': 'metric.metric_id',
        'on_delete': None,
        'on_update': None,
    }

    _alter_constraint(migrator, new)
