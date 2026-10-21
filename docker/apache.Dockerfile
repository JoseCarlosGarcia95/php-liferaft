ARG BASE_IMAGE=debian:bookworm-slim@sha256:7ff6ba31527b9e336162fa061746c366c4b2032f4d2cff2078bea43f78efe3f8
FROM ${BASE_IMAGE} AS os
ARG DEBIAN_SNAPSHOT=20261020T000000Z
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s/ bookworm main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/%s/ bookworm main\ndeb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/%s/ bookworm-security main\n' "$DEBIAN_SNAPSHOT" "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends ca-certificates libxml2 libsqlite3-0 libonig5 libstdc++6 apache2 \
    && rm -rf /var/lib/apt/lists/*

FROM os AS compiler
RUN apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends autoconf bison re2c build-essential pkg-config libxml2-dev libsqlite3-dev libonig-dev xz-utils apache2-dev \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_ARCHIVE
ARG SOURCE_SHA256
ARG MAKE_JOBS=4
ARG EXTRA_CONFIGURE=""
COPY ${SOURCE_ARCHIVE} /tmp/php.tar.xz
COPY docker/build-php-apache.sh /usr/local/bin/build-php-apache
RUN printf '%s  /tmp/php.tar.xz\n' "$SOURCE_SHA256" | sha256sum -c - \
    && MAKE_JOBS="$MAKE_JOBS" EXTRA_CONFIGURE="$EXTRA_CONFIGURE" sh /usr/local/bin/build-php-apache /tmp/php.tar.xz \
    && rm /tmp/php.tar.xz

FROM os AS apache
COPY --from=compiler /usr/local/ /usr/local/
COPY --from=compiler /usr/lib/apache2/modules/ /usr/lib/apache2/modules/
COPY --from=compiler /etc/apache2/mods-available/ /etc/apache2/mods-available/
COPY docker/apache/mpm_prefork.conf /etc/apache2/mods-available/mpm_prefork.conf
COPY docker/apache/phpup.conf /etc/apache2/conf-enabled/phpup.conf
COPY docker/php-apache.ini /usr/local/etc/php/php.ini
RUN a2dismod mpm_event \
    && a2enmod mpm_prefork \
    && if [ -f /etc/apache2/mods-available/php.load ]; then a2enmod php; \
       elif [ -f /etc/apache2/mods-available/php7.load ]; then a2enmod php7; \
       elif [ -f /etc/apache2/mods-available/php5.load ]; then a2enmod php5; \
       else echo 'no Apache PHP module was installed' >&2; exit 1; fi \
    && mkdir -p /var/lib/php/sessions /var/www/html \
    && chmod 1777 /var/lib/php/sessions
ARG SOURCE_SHA256
ARG SOURCE_URL=https://github.com/JoseCarlosGarcia95/php2shell-temporal-bugfix
ARG SOURCE_VERSION=unknown
ARG PROJECT_REVISION=0
ARG REPOSITORY_REVISION=uncommitted
LABEL org.opencontainers.image.source="$SOURCE_URL" \
      org.opencontainers.image.revision="$REPOSITORY_REVISION" \
      org.opencontainers.image.version="$SOURCE_VERSION-up.$PROJECT_REVISION" \
      io.phpup.project.revision="$PROJECT_REVISION" \
      io.phpup.source.sha256="$SOURCE_SHA256" \
      io.phpup.server="apache-mod-php"
WORKDIR /var/www/html
EXPOSE 80
STOPSIGNAL SIGWINCH
ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
