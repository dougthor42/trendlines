Development
===========

Assumptions:

+ Docker and Docker-compose are installed and up-to-date
+ Python 3.6 or higher


1.  Clone the repository::

    $ git clone git@github.com:dougthor42/trendlines.git

2.  Move into the directory, make a virutal environment, and activate it:

    .. code-block:: shell

      $ cd trendlines
      $ python -m venv .venv
      $ . .venv/bin/activate

3.  Install requirements:

    .. code-block:: shell

      $ pip install -U pip setuptools wheel
      $ pip install -r requirements.txt -r requirements-dev.txt


4.  Run tests:

    .. code-block:: shell

      $ pytest


Running with scripts
--------------------

Make sure the `config/localhost.cfg` file exists:

.. code-block:: python

   # ./config/localhost.cfg
   DEBUG = True
   DATABASE = "./internal.db"
   TRENDLINES_API_URL = "http://localhost:5000/api/v1/data"
   broker_url = "redis://localhost"

In 3 separate shells, run these 3 commands in order

1.  ``docker run -p 6379:6379 redis``
2.  ``python runworker.py``
3.  ``python runserver.py``

You can also optionally run each in the background (``-d`` for docker and
``&`` for the others), but personally I like to see the logs scroll by.

From a 4th shell, send data using the plaintext protocol:

.. code-block:: shell

   echo "metric.name 12.345 `date +%s`" | nc localhost 2003

And view the data by opening ``http://localhost:5000`` in your browser.


Running with Docker-Compose
---------------------------

The default configuration assumes running within docker-compose. If you need
different settings, create ``config/trendlines.cfg`` and add your variables
to it.

Build the images and bring up the stack:

.. code-block:: shell

   $ docker-compose -f docker-build.yml build
   $ docker-compose -f docker-build.yml up

Send data in

.. code-block:: shell

   echo "metric.name 12.345 `date +%s`" | nc localhost 2003

And view the data by opening ``http://localhost:5000`` in your browser.


Building the Docker Image
-------------------------

This is handled in CI, but in case you need to do it manually:

.. code-block:: shell

   docker build -f docker/Dockerfile -t trendlines:latest -t dougthor42/trendlines:latest .
   docker push dougthor42/trendlines:latest


Database Migrations
-------------------

This project uses `peewee-moves`_ to handle migrations. The documentation
for that project is a little lacking, but I found it a litte easier to use
than the more-popular `peewee-migrate`_. `peewee-moves`_ also has more
documentation.

.. _`peewee-moves`: https://github.com/timster/peewee-moves
.. _`peewee-migrate`: https://github.com/klen/peewee_migrate

To apply migrations to an exsiting database that has **never had any
migrations applied**:

1.  Open the database.
2.  Manually create the following table (adjust syntax accordingly):

    .. code-block:: sql

       CREATE TABLE migration_history (
         `id` INT NOT NULL AUTO_INCREMENT,
         `name` VARCHAR(255) NOT NULL,
         `date_applied` DATETIME NOT NULL,
       PRIMARY_KEY (`id`));

3.  Populate the table with all the migrations that have already been
    applied. The ``name`` value should match the migration filename, sans
    ``.py`` extension, and the ``date_applied`` field can be any timestamp.

    .. code-block:: sql

       INSERT INTO `migration_history`
         (`name`, `date_applied`)
         VALUES
           ('0001_create_table_metric', '2019-02-14 14:56:37'),
           ('0002_create_table_datapoint', '2019-02-14 14:56:37');

4.  Verify that things are working. You should see ``[x]`` for all migrations:

    .. code-block:: shell

       $ peewee-db --directory migrations --database sqlite:///internal.db status
       INFO: [x] 0001_create_table_metric
       INFO: [x] 0002_create_table_datapoint


Creating a New Table
^^^^^^^^^^^^^^^^^^^^

1.  Create the table in ``trendlines.orm``.
2.  Create the new table migration:

    .. code-block:: shell

       $ peewee-db --directory migrations \
                   --database sqlite:///internal.db \
                   create \
                   trendlines.orm.NewTable

3.  And then apply it:

    .. code-block:: shell

       $ peewee-db --directory migrations \
                   --database sqlite:///internal.db \
                   upgrade

    If you're using the python shell, run the following for for step 3:

    .. code-block:: python

       >>> from peewee import SqliteDatabase
       >>> from peewee_moves import DatabaseManager
       >>> manager = DatabaseManager(SqliteDatabase('internal.db')
       >>> manager.create('trendlines.orm')
       >>> manager.upgrade()


Modifying a Table
^^^^^^^^^^^^^^^^^

1.  Modify the table in ``trendlines.orm``.
2.  Create the migration file:

    .. code-block:: shell

       $ peewee-db --directory migrations \
                   --database sqlite:///internal.db \
                   revision
                   "short_revision_description spaces OK but not recommended"

3.  Manually modify the ``upgrade`` and ``downgrade`` scripts in the new
    migration file.
4.  Apply the migration:

    .. code-block:: shell

       $ peewee-db --directory migrations \
                   --database sqlite:///internal.db \
                   upgrade
