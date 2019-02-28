"""
create table metric
date created: 2019-02-14 22:01:44.111130
"""


def upgrade(migrator):
    with migrator.create_table('metric') as table:
        table.int('metric_id', primary_key=True)
        table.char('name', max_length=120)
        table.char('units', max_length=24, null=True)


def downgrade(migrator):
    migrator.drop_table('metric')
