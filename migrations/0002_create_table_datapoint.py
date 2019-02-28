"""
create table datapoint
date created: 2019-02-14 22:01:50.586924
"""


def upgrade(migrator):
    with migrator.create_table('datapoint') as table:
        table.int('datapoint_id', primary_key=True)
        table.foreign_key(
            'INT',
            'metric_id',
            on_delete=None,
            on_update=None,
            references='metric.metric_id',
        )
        table.float('value')
        table.int('timestamp')


def downgrade(migrator):
    migrator.drop_table('datapoint')
