#!/bin/sh
set -eu

mkdir -p /tmp/session-source /module
tar -xJf "$1" -C /tmp/session-source --strip-components=1
python3 - <<'PY'
import json
sdk = json.load(open('/usr/local/share/phpup/manifest.json'))
source = json.load(open('/tmp/session-source/phpup/manifest.json'))
if source['abi_id'] != sdk['abi_id'] or source['version'] != sdk['version']:
    raise SystemExit('session source does not match the SDK core/toolchain identity')
PY
cd /tmp/session-source/ext/session
phpize
export CFLAGS="-O2 -g -fcommon"
./configure --with-php-config=/usr/local/bin/php-config --enable-session=shared
make -j 4
cp modules/session.so /module/session.so
python3 - <<'PY'
import hashlib
import json
import os
import platform
import subprocess
source = json.load(open('/tmp/session-source/phpup/manifest.json'))
extension_dir = subprocess.check_output(['php-config', '--extension-dir'], text=True).strip()
metadata = {
    'source': source,
    'sdk_image_id': os.environ['SDK_IMAGE_ID'],
    'architecture': platform.machine(),
    'php_api': extension_dir.rsplit('-', 1)[-1],
    'php_build': json.loads(subprocess.check_output(['php', '-n', '-r',
        'echo json_encode(array("version" => PHP_VERSION, "zts" => PHP_ZTS, "debug" => PHP_DEBUG, "int_size" => PHP_INT_SIZE));'], text=True)),
    'module_sha256': hashlib.sha256(open('/module/session.so', 'rb').read()).hexdigest(),
}
with open('/module/session.json', 'w') as output:
    json.dump(metadata, output, indent=2, sort_keys=True)
    output.write('\n')
with open('/module/session.sha256', 'w') as output:
    output.write(metadata['module_sha256'] + '  session.so\n')
PY
