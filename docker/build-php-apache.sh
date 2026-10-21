#!/bin/sh
set -eu

mkdir -p /usr/src/php /usr/local/etc/php
tar -xJf "$1" -C /usr/src/php --strip-components=1
cd /usr/src/php

export CFLAGS="-O2 -g -fcommon"
set -- --disable-all --enable-session --enable-filter --enable-tokenizer \
    --without-pear --disable-cli --disable-cgi --disable-fpm --disable-phpdbg \
    --with-apxs2=/usr/bin/apxs2 --with-config-file-path=/usr/local/etc/php \
    --with-config-file-scan-dir=/usr/local/etc/php/conf.d
for option in ${EXTRA_CONFIGURE:-}; do
    set -- "$@" "$option"
done
if ! ./configure "$@" > /tmp/apache-configure.log 2>&1; then
    cat /tmp/apache-configure.log
    exit 1
fi
if ! make -j "${MAKE_JOBS:-4}" > /tmp/apache-build.log 2>&1; then
    cat /tmp/apache-build.log
    exit 1
fi
make install
make clean > /dev/null
rm -f /tmp/apache-configure.log /tmp/apache-build.log
