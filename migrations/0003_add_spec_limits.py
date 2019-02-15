"""
add_spec_limits
date created: 2019-02-14 23:30:21.963046
"""


def upgrade(migrator):
    migrator.add_column('metric', 'upper_limit', 'float', null=True)
    migrator.add_column('metric', 'lower_limit', 'float', null=True)


def downgrade(migrator):
    migrator.drop_column('metric', 'lower_limit')
    migrator.drop_column('metric', 'upper_limit')
