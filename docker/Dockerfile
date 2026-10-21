ARG BASE_IMAGE=debian:bookworm-slim@sha256:7ff6ba31527b9e336162fa061746c366c4b2032f4d2cff2078bea43f78efe3f8
FROM ${BASE_IMAGE} AS os
ARG DEBIAN_SNAPSHOT=20261020T000000Z
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s/ bookworm main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/%s/ bookworm main\ndeb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/%s/ bookworm-security main\n' "$DEBIAN_SNAPSHOT" "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends ca-certificates libxml2 libsqlite3-0 libonig5 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

FROM os AS compiler
RUN apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends autoconf bison re2c build-essential pkg-config libxml2-dev libsqlite3-dev libonig-dev xz-utils python3 valgrind \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_ARCHIVE
ARG SOURCE_SHA256
ARG MAKE_JOBS=4
COPY ${SOURCE_ARCHIVE} /tmp/php.tar.xz
COPY docker/build-php.sh /usr/local/bin/build-php
RUN printf '%s  /tmp/php.tar.xz\n' "$SOURCE_SHA256" | sha256sum -c - \
    && MAKE_JOBS="$MAKE_JOBS" sh /usr/local/bin/build-php /tmp/php.tar.xz \
    && rm /tmp/php.tar.xz
COPY docker/php.ini /usr/local/etc/php/php.ini
COPY docker/php-fpm.conf /usr/local/etc/php-fpm.conf
RUN mkdir -p /usr/local/etc/php/conf.d /var/lib/php/sessions \
    && printf 'extension=session.so\n' > /usr/local/etc/php/conf.d/session.ini \
    && chmod 1777 /var/lib/php/sessions

FROM compiler AS sdk
WORKDIR /usr/src/php
CMD ["/bin/sh"]

FROM os AS runtime
COPY --from=compiler /usr/local/ /usr/local/
RUN mkdir -p /var/lib/php/sessions /var/www/html \
    && chmod 1777 /var/lib/php/sessions
ARG SOURCE_SHA256
ARG SOURCE_URL=https://github.com/JoseCarlosGarcia95/php-liferaft
ARG SOURCE_VERSION=unknown
ARG PROJECT_REVISION=0
ARG REPOSITORY_REVISION=uncommitted
LABEL org.opencontainers.image.source="$SOURCE_URL" \
      org.opencontainers.image.revision="$REPOSITORY_REVISION" \
      org.opencontainers.image.version="$SOURCE_VERSION-up.$PROJECT_REVISION" \
      io.phpup.project.revision="$PROJECT_REVISION" \
      io.phpup.source.sha256="$SOURCE_SHA256"
WORKDIR /var/www/html

FROM runtime AS cli
ENTRYPOINT ["php"]
CMD ["--version"]

FROM runtime AS fpm
EXPOSE 9000
STOPSIGNAL SIGQUIT
ENTRYPOINT ["php-fpm", "-F", "-y", "/usr/local/etc/php-fpm.conf"]

FROM sdk AS session-module
ARG SOURCE_ARCHIVE
ARG SOURCE_SHA256
COPY ${SOURCE_ARCHIVE} /tmp/php.tar.xz
COPY docker/build-session.sh /usr/local/bin/build-session
RUN printf '%s  /tmp/php.tar.xz\n' "$SOURCE_SHA256" | sha256sum -c - \
    && sh /usr/local/bin/build-session /tmp/php.tar.xz

FROM scratch AS session-export
COPY --from=session-module /module/ /
