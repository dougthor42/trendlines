# Changelog for Trendlines


## Unreleased
+ [BREAKING] Updated REST API: "add" and "get" changed to "data". The HTTP
  method will be used to determine adding or retrieving.
+ Implemented switching between sequential and time-series data. (#8).


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
