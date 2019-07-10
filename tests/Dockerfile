# This Dockerfile creates a dummy host that mimics my typical
# setup for Apache2 and proxied services.

FROM "ubuntu:18.04" as ubuntu-docker-apache

LABEL maintainer="doug.thor@gmail.com"

RUN apt update \
    && apt install -y \
        apache2 \
        # Docker prereqs
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common

# Docker
RUN curl \
        -fsSL \
        https://download.docker.com/linux/ubuntu/gpg \
        | apt-key add - \
    && add-apt-repository \
        "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) \
        stable" \
    && apt update \
    # Installing docker takes a long time because many dependencies are
    # missing from our base image.
    && apt install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io

# Install docker-compose
# Technically it's not needed because the test runner is actually
# using the compose file, but this helps mimic a live server.
RUN curl \
        -L \
        "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o \
        /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && apt-get clean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 80

# Run apache in the foreground
CMD ["apache2ctl", "-D", "FOREGROUND", "-e", "INFO"]


# Now that we have a base "server", we install our application
# on it. This should match closely with the docker-compose installation
# instructions.
FROM ubuntu-docker-apache

RUN mkdir -p /var/www/trendlines

RUN apt update && apt install -y vim
RUN apt install -y dnsutils iputils-ping less
RUN echo foo

COPY integration/apache.conf /etc/apache2/sites-available/main.conf
COPY integration/trendlines.cfg /var/www/trendlines/trendlines.cfg

RUN chown www-data:www-data /var/www/trendlines \
    && a2ensite main.conf \
    && a2enmod proxy \
    && a2enmod proxy_http \
    && a2enmod headers \
    && a2dissite 000-default.conf \
    && service apache2 restart
