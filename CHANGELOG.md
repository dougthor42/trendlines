# Changelog for Trendlines


## Unreleased
+ `create_db` was moved out of `app_factory.py` and into `orm.py`. (#115)


## 0.5.0 (2019-02-28)

### Notes
Upgrading from 0.4.0 to 0.5.0 breaks the migration history of the
database. **Automatic upgrades are not supported.** In order to correctly
upgrade without losing your data, follow these instructions (assuming
docker-compose):

> Note: you may need to add `sudo` to most of these.

1.  Bring `trendlines` down: `docker-compose down`.
2.  Backup your database: `cp internal.db internal.db_old`
3.  Pull the new `trendlines` code: `docker-compose pull`
4.  Make a new, empty database file (see issue #110):
    ```bash
    $ touch internal.db
    $ chown www-data:www-data internal.db
    ```
5.  Run the migrations on this new file:
    ```bash
    $ docker-compose run --rm --no-deps trendlines \
          peewee-db \
              --directory /trendlines/migrations \
              --database sqlite:///data/internal.db \
              status
    $ docker-compose run --rm --no-deps trendlines \
          peewee-db \
              --directory /trendlines/migrations \
              --database sqlite:///data/internal.db \
              upgrade
    ```
    You should see the following outputs, perhaps with a "Creating network"
    thrown in there from docker:
    ```
    INFO: [ ] 0001_create_table_metric
    INFO: [ ] 0002_create_table_datapoint
    INFO: [ ] 0003_add_spec_limits
    INFO: [ ] 0004_unique_constraint_metric_name
    INFO: [ ] 0005_on_delete_cascade_metric

    INFO: upgrade: 0001_create_table_metric
    INFO: upgrade: 0002_create_table_datapoint
    INFO: upgrade: 0003_add_spec_limits
    INFO: upgrade: 0004_unique_constraint_metric_name
    INFO: upgrade: 0005_on_delete_cascade_metric
    ```
6.  Copy your data from the old file to the new:
    ```
    $ sqlite3 internal.db
    sqlite> ATTACH 'internal.db_old' as old;
    sqlite> INSERT INTO metric SELECT * FROM old.metric;
    sqlite> INSERT INTO datapoint SELECT * FROM old.datapoint;
    sqlite> .q
    ```
7.  Bring up `trendlines`: `docker-compose up -d`
8.  Verify that you can add a new metric and datapoint:
    ```bash
    $ echo "some-new-metric-name 99" | nc $SERVER $PORT
    ```

### Changes
+ Fixed an issue with migrations (#112).


## 0.4.0 (2019-02-26)

### New Features
+ Added columns to the `Metric` table to support limits. (#65)
+ Many more API routes have been added:
    + `GET /api/v1/metric/<metric_name>` has been implemented (#73)
    + `DELETE /api/v1/metric/<metric_name>` has been implemented (#78)
    + `POST /api/v1/metric` has been implemented (#74)
    + `PUT /api/v1/metric/<metric_name>` has been implemented (#75)
    + `PATCH /api/v1/metric/<metric_name>` has been implemented (#83)
    + `DELETE /api/v1/datapoint/<datapoint_id>` has been implemented (#57)
+ Implemented database migrations (#62)
+ The program version is now displayed on all pages. (#109)
+ The tree is now auto-expanded by default. (#105)

### Changes
+ Changed (again) how we handle being behind a proxy. (#60)
+ DB migrations are now inlcuded in the docker image, and documentation
  was added on how to perform upgrades. (#67)
+ The `Metric.name` column is now forced to be unique. Previously this was
  enforced on the software side, but not on the database side. (#66)
+ The `DataPoint.metric_id` foreign key is now set to CASCADE on deletes (#69)
+ Error responses for the REST API have been refactored (#85)
+ Additional tests for PUT/PATCH metric have been added (#86)
+ Make use of peewee's `playhouse` extensions for converting model instances
  to and from dicts. (#87)
+ `peewee-moves` was updated to v2.0.1.
+ Documentation is now reStructuredText and is hosted by ReadTheDocs (#91)
+ Switched to using `loguru` for logging. (#94)
+ Renamed some function arguments to be more clear. (#89)
+ Removed a hack that caused plot urls to be generated client-side. Was
  blocking #47. (#100)
+ Moved javascript out of HTML files. (#47)


## v0.3.0 (2019-01-28)
+ `units` are now also returned in the GET `/data` API call.
+ Removed a confusing route: `/api/v1/<metric>`. (#39)
+ Added a title that will link back to the index page. (#40)
+ Changed the way we handle generating links when behind a proxy that's
  mucking about with the URLs. (#41)
+ Units will now be displayed on the y-axis if they exist. (#37)
+ `routes.format_data` was moved to the `utils` module.
+ Added support for optional Celery workers that accept TCP data, allowing
  for easier transition from `Graphite`. (#6)


## v0.2.0 (2019-01-14)
+ [BREAKING] Updated REST API: "add" and "get" changed to "data". The HTTP
  method will be used to determine adding or retrieving.
+ Implemented switching between sequential and time-series data. (#8).
+ Plot link generation has been moved client-side. This fixes an issue where
  links would not work when an external force modifies the URL. Fixes #33.


## v0.1.1 (2019-01-10):
Simply a version bump to verify deployment to PyPI from Travis-CI.


## v0.1.0 (2019-01-10): Preview Release
This is a preview release with the core functionality:

+ Web page for viewing data with tree structure (#7)
+ Accept TCP entries via HTTP POST
+ Docker container for easy deployment (#9)
+ Unit and integration tests (#4)
+ Continuous Integration for tests (#10)

What's not included is:

+ Accept UDP data (#6)
+ Switch between by-number and by-time plots (#8)
+ Looking nice
+ UX enhancements
+ Multiple plots per page (#11)
+ Email alerting system (#12)
+ Continuous Delivery to PyPI and Docker Hub


## v0.0.0 (2018-12-20)
+ Project Creation
