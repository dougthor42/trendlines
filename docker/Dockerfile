FROM python:3.7.1-slim-stretch

LABEL maintainer="doug.thor@gmail.com"

ENV WSGI_VERSION="4.6.5"

# Install Requirements
RUN apt-get update \
    && apt-get install -y \
        apache2 \
        apache2-dev \
        make \
        wget \
    # Install mod_wsgi from source for our specific python version
    && wget \
        -O mod_wsgi-$WSGI_VERSION.tar.gz \
        "https://github.com/GrahamDumpleton/mod_wsgi/archive/$WSGI_VERSION.tar.gz" \
    && tar -xzf mod_wsgi-$WSGI_VERSION.tar.gz \
    && cd mod_wsgi-$WSGI_VERSION \
    && ./configure \
    && make \
    && make install \
    && cd / \
    # Cleanup
    && rm -rf mod_wsgi-$WSGI_VERSION* \
    && apt-get remove -y apache2-dev wget make \
    && apt-get clean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 80

# Run apache in the foreground
CMD ["apache2ctl", "-D", "FOREGROUND", "-e", "INFO"]

### Now that the base stuff is done with, actually install the app.
COPY requirements.txt /requirements.txt
RUN pip install \
    -r /requirements.txt \
    && rm /requirements.txt

COPY apache/wsgi.py /var/www/wsgi.py
COPY apache/trendlines.conf /etc/apache2/sites-available/trendlines.conf
COPY docker/trendlines.cfg /data/trendlines.cfg
COPY setup.py /trendlines/
COPY README.md /trendlines/
COPY ./migrations /trendlines/migrations
COPY ./src /trendlines/src

# TODO: Replace with install from pypi? Not if I want things built off master.
RUN pip install -e /trendlines

RUN a2ensite trendlines \
    && a2dissite 000-default.conf \
    && chown -R www-data:www-data /data


# vim: tabstop=4 shiftwidth=4 expandtab filetype=dockerfile
