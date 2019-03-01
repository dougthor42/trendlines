Upgrading
=========

Docker
------

Upgrading via pure Docker is not supported, as that's intended to only be
used as a preview. Please see Docker-Compose.


Docker Compose
--------------

Upgrading ``trendlines`` when running in Docker Compose is as easy as pulling
the new image. Upgrading should take less than 5 minutes, depending on your
connection speed.

1.  Update your ``docker-compose.yml`` file if needed.
2.  Bring down your service. We don't want anything trying to write changes
    while we're doing things.
3.  Backup your database.
4.  Pull the new image.
5.  (Optional) Manually perform database migrations. As of #117 (release
    v0.6.0), migrations are automatically performed upon recieving the first
    request after server start (when the WSGI process starts).
6.  Bring up the stack.

If you're using a specific version release, update your ``docker-compose.yml``
file:

.. code-block:: yaml

   image: dougthor42/trendlines:1.1

.. note::

   Make sure to update the version in both the ``trendlines`` service
   **and the** ``celery`` **service.**

If you're using the ``latest`` docker tag, which points to the latest git-tagged
release, then no changes to ``docker-compose.yml`` are needed.

Then run the rest of the steps:

.. code-block:: bash

   $ cd /var/www/trendlines
   $ docker-compose down
   $ cp internal.db internal.db.bak
   $ docker-compose pull

   # Optional: See what migrations are missing
   $ docker-compose run --rm --no-deps trendlines \
       peewee-db \
           --directory /trendlines/migrations \
           --database sqlite:///data/internal.db \
           status

   # Optional: Run the migrations
   $ docker-compose run --rm --no-deps trendlines \
       peewee-db \
           --directory /trendlines/migrations \
           --database sqlite:///data/internal.db \
           upgrade
   $ docker-compose up -d
