# Changelog for Trendlines


## Unreleased
+ Implemented database migrations (#62)
+ Changed (again) how we handle being behind a proxy. (#60)


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
