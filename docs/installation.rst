Installation
============

There are multiple ways to install ``Trendlines`` depending on your needs.
Some methods are admittely more supported than others, and I'm sorry about
that.

+ `Docker`_: Good for trying out ``Trendlines`` to see if you like it.
+ `Docker Compose`_: The recommended way for deploying to a production
  environment.
+ `Direct Install`_: When you have a dedicated server to run things. Though
  I'd still recommend using a `Docker Compose`_ install.


Docker
------

The easiest way to get up and running with ``Trendlines`` is with Docker:

.. code-block:: bash

   $ docker run -p 5000:80 dougthor42/trendlines:latest

Then open a browser to ``http://localhost:5000/`` and you're all set. Add some data
(see below) and refresh the page.

.. warning::

   Data will not persist when the container is destroyed!


Docker Compose
--------------

.. note::

   **WIP!**

If you're doing more than just playing around, you'll likely want to set up
Docker Compose. I've included an example Compose file `in the repo`_.

.. _`in the repo`: https://github.com/dougthor42/trendlines/blob/master/docker/docker-compose.yml

Before using the example Compose file, you'll need to:

1. Make a directory to store the config file (and database file if using
   SQLite)
2. Make sure that dir is writable by docker-compose.
3. Create the configuration ``trendlines.cfg`` within that directory.

.. code-block:: bash

   $ mkdir /var/www/trendlines
   $ chmod -R a+w /var/www/trendlines
   $ touch /var/www/trendlines/trendlines.cfg

Next, edit your new ``trendlines.cfg`` file as needed. At the very least, the
following is needed:

.. code-block:: python

   # /var/www/trendlines/trendlines.cfg
   SECRET_KEY = b"don't use the value written in this README file!"
   DATABASE = "/data/internal.db"

.. tip::

   You can generate a secure secret key from the python REPL like so:

   .. code-block:: python

      >>> import os
      >>> import binascii
      >>> binascii.hexlify(os.urandom(32))
      b'<some string of hex [0-9a-f]>'

   Which you can then copy into ``trendlines.cfg``'s ``SECRET_KEY`` field.
   Don't forget the leading ``b``!

You should be all set to bring Docker Compose up:

.. code-block:: bash

   $ docker-compose -f path/to/docker-compose.yml up -d

Again, open up a browser to ``http://localhost`` and you're good to go. Add some
data as outlined below and start playing around.

.. tip::

   If you get an error complaining about "Error starting userland proxy:
   Bind for 0.0.0.0:80: Unexpected error Permission denied", then try changing
   the port in ``docker-compose.yml`` to something else. I like 5000 myself:

   .. code-block:: yaml

      ports:
        - 5000:80

   and then navigate to ``http://localhost:5000`` in your browser.


Direct Install
--------------

.. attention::

   Not yet supported.


Running behind a proxy
----------------------

A typical case, for me at least, is adding this application to a server that's
already running Apache for other things. In this case, make the following
adjustments:

1.  Add a proxy to the ``VirtualHost`` in your apache config.
2.  Make sure to set the ``URL_PREFIX`` variable in your Trendlines config file.
3.  Have the following apache mods enabled:
    + ``mod_proxy``
    + ``mod_proxy_http``
    + ``mod_headers``

.. code-block:: apache

   # /etc/apache2/sites-enabled/your-site.conf
   <VirtualHost *:80>
       # optionally replace all instances of "trendlines" with whatever you want
       # Make sure the port on ProxyPass and ProxyPassReverse matches what is
       # exposed in your docker-compose.yml file.
       <Location /trendlines>
           ProxyPreserveHost On
           ProxyPass http://0.0.0.0:5082/trendlines
           ProxyPassReverse http://0.0.0.0:5082/trendlines

           RequestHeader set X-Forwarded-Port 80
       </Location>
   </VirtualHost>


.. code-block:: python

   # /var/www/trendlines/trendlines.cfg
   URL_PREFIX = "/trendlines"    # Whatever you put in your Apache proxy


Running with Celery
-------------------

Add the following services to your ``docker-compose.yml``:

.. code-block:: yaml

   redis:
     image: redis
     ports:
       - "6379:6379"
   celery:
     image: dougthor42/trendlines:latest
     ports:
       - "2003:2003"
     volumes:
       # should be the same as what's in the 'trendlines' service
       - type: bind
         source: /var/www/trendlines
         target: /data
     command: celery worker -l info -A trendlines.celery_app.celery
     depends_on:
       - "redis"
