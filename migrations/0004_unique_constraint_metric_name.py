"""
unique_constraint_metric.name
date created: 2019-02-18 16:23:33.621724
"""


def upgrade(migrator):
    migrator.add_index("metric", ["name"], unique=True)


def downgrade(migrator):
    migrator.drop_index("metric", ["name"])
