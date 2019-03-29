"""
make_primary_keys_autoincrement
date created: 2019-03-28 21:47:26.858802
"""

# Reminders:
# + 'single_quotes' denote string literals.
# + "double_quotes" denote identifiers.
#     + same with [brackets] and `backticks`, for compatability with MS SQL
#       and MySQL.
#       -- https://www.sqlite.org/lang_keywords.html
# + "So, in most real systems, an index should be created on the child key
#   columns of each foreign key constraint."
#   -- https://www.sqlite.org/foreignkeys.html

# Downgrade to the original DDL
DOWNGRADE = """
ALTER TABLE "metric" RENAME TO "metric_temp";
CREATE TABLE IF NOT EXISTS "metric" (
  "metric_id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(120) NOT NULL,
  "units" VARCHAR(24),
  "upper_limit" REAL,
  "lower_limit" REAL
);
INSERT INTO "metric" SELECT * FROM "metric_temp";
DROP TABLE "metric_temp";
CREATE UNIQUE INDEX "metric_name" ON "metric" ("name");

ALTER TABLE "datapoint" RENAME TO "datapoint_temp";
CREATE TABLE IF NOT EXISTS "datapoint" (
  "datapoint_id" INTEGER NOT NULL PRIMARY KEY,
  "metric_id" INTEGER NOT NULL,
  "value" REAL NOT NULL,
  "timestamp" INTEGER NOT NULL,
  FOREIGN KEY ("metric_id") REFERENCES "metric" ("metric_id") ON DELETE CASCADE
);
INSERT INTO "datapoint" SELECT * FROM "datapoint_temp";
DROP TABLE "datapoint_temp";
CREATE INDEX "fakemodel_metric_id" ON "datapoint" ("metric_id");
"""

# New DDL
UPGRADE = """
ALTER TABLE "metric" RENAME TO "metric_temp";
CREATE TABLE IF NOT EXISTS "metric" (
  "metric_id"  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name"  VARCHAR(120) NOT NULL,
  "units"  VARCHAR(24),
  "upper_limit"  REAL,
  "lower_limit"  REAL
);
INSERT INTO "metric" SELECT * FROM "metric_temp";
DROP TABLE "metric_temp";
CREATE UNIQUE INDEX "metric_name" ON "metric" ("name");

ALTER TABLE "datapoint" RENAME TO "datapoint_temp";
CREATE TABLE IF NOT EXISTS "datapoint" (
  "datapoint_id"  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "metric_id"  INTEGER NOT NULL,
  "value"  REAL NOT NULL,
  "timestamp"  INTEGER NOT NULL,
  FOREIGN KEY("metric_id") REFERENCES "metric" ( "metric_id" ) ON DELETE CASCADE
);
INSERT INTO "datapoint" SELECT * FROM "datapoint_temp";
DROP TABLE "datapoint_temp";
CREATE INDEX "datapoint_metric_id" ON "datapoint" ("metric_id");
"""


def upgrade(migrator):
    for line in UPGRADE.split(";"):
        sql = line + ";"    # not really needed, but gives me warm fuzzies.
        migrator.execute_sql(sql)


def downgrade(migrator):
    for line in DOWNGRADE.split(";"):
        sql = line + ";"    # not really needed, but gives me warm fuzzies.
        migrator.execute_sql(sql)
