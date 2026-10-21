#!/bin/sh
set -eu

mkdir -p /usr/src/php /usr/local/share/phpup /usr/local/etc/php/conf.d
tar -xJf "$1" -C /usr/src/php --strip-components=1
cd /usr/src/php
cp phpup/manifest.json /usr/local/share/phpup/manifest.json

set -- --disable-all --enable-cli --enable-cgi --enable-fpm \
    --enable-session=shared --enable-filter --enable-tokenizer --without-pear \
    --disable-phpdbg --with-config-file-path=/usr/local/etc/php \
    --with-config-file-scan-dir=/usr/local/etc/php/conf.d
# Manifest validation restricts each extra option to a single shell-safe word.
for option in $(python3 -c 'import json; print(" ".join(json.load(open("phpup/manifest.json"))["configure"]))'); do
    set -- "$@" "$option"
done
export CFLAGS="-O2 -g -fcommon"
printf 'Configuring PHP from %s\n' "$1"
if ! ./configure "$@" > /tmp/php-configure.log 2>&1; then
    cat /tmp/php-configure.log
    exit 1
fi
printf 'Compiling PHP with %s jobs\n' "${MAKE_JOBS:-4}"
if ! make -j "${MAKE_JOBS:-4}" > /tmp/php-build.log 2>&1; then
    cat /tmp/php-build.log
    exit 1
fi
make install
make clean > /dev/null
rm -f /tmp/php-build.log /tmp/php-configure.log
