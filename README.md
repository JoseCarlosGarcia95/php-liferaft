# php2shell-temporal-bugfix

Inspectable PHP security backports, source archives, and Docker CLI, FPM, and Apache + mod_php builds.
This personal project covers final EOL releases and selected current PHP releases.
It is independently maintained; project revisions describe the exact included
patches rather than implying official PHP support or complete vulnerability coverage.

## Versions

[`versions.json`](versions.json) is the authoritative source manifest. Checksums
come from PHP's official release metadata and are checked for every source build.

| Branch | Upstream base | Patch directory |
| --- | --- | --- |
| 5.6 | 5.6.40 | [patches/5.6](patches/5.6) |
| 7.0 | 7.0.33 | [patches/7.0](patches/7.0) |
| 7.1 | 7.1.33 | [patches/7.1](patches/7.1) |
| 7.2 | 7.2.34 | [patches/7.2](patches/7.2) |
| 7.3 | 7.3.33 | [patches/7.3](patches/7.3) |
| 7.4 | 7.4.33 | [patches/7.4](patches/7.4) |
| 8.0 | 8.0.30 | [patches/8.0](patches/8.0) |
| 8.1 | 8.1.34 | [patches/8.1](patches/8.1) |
| 8.2 | 8.2.35 | official release |
| 8.3 | 8.3.36 | official release |
| 8.4 | 8.4.27 | official release |
| 8.5 | 8.5.12 | official release |

## Fixed CVEs

PHP 8.2.35, 8.3.36, 8.4.27 and 8.5.12 contain the official fixes for
CVE-2026-109618 and CVE-2026-109619 and are the bases used for those branches.
No local CVE fix is claimed for the EOL branches: their patches are independent
hardening, not a complete official-equivalent backport. The generated table below
lists only independently verified local fixes.

<!-- phpup:fixed-cves:start -->

No independently verified CVE fixes are claimed yet. See the reported issues below.

<!-- phpup:fixed-cves:end -->

### Reported upload-progress issues

The [official PHP advisory](https://www.php.net/archive/2026.php#2026-10-21-5)
describes two critical remote-code-execution issues:

- **CVE-2026-109618, RCE via OOM corruption:** out-of-memory handling can
  interrupt PHP while request data is only partially initialized; cleanup may
  then treat the invalid data as valid.
- **CVE-2026-109619, RCE via stale global state:** request-owned internal state
  can survive after its backing memory is freed; a later request on the same
  worker may use it before normal initialization resets it.

All web SAPIs are affected, with the highest risk reported for Apache mod_php.
The official patched releases are 8.2.35, 8.3.36, 8.4.27 and 8.5.12. The advisory
states there are no complete mitigations; updating is the only safe choice.

### Serializer context lifecycle

The official fix adds `php_basic_early_rinit()`, which resets the same
`BG(serialize)` / `BG(unserialize)` / `serialize_lock` state before
`php_hash_environment()`, along with the session and allocator changes for
CVE-2026-109618. PHP 8.2-8.5 use the official patched releases directly. For the
EOL branches, `serializer-context-reset.patch` applies an equivalent early reset
as independent hardening; it does not include the full official allocator fix.

PHP's [official announcement](https://www.php.net/archive/2026.php#2026-10-20-1)
schedules two critical fixes for 21 October 2026 at 14:00 UTC; the article's
identifiers must be reconciled with the official advisories once published.

## Build source archives

Requirements: Python **3.12+**, `patch` (GNU patch on Linux), and Internet access to
the official PHP download servers. Python dependencies are standard-library only.

```sh
python3 scripts/phpup.py validate
python3 scripts/phpup.py prepare --branch 8.2
python3 scripts/phpup.py prepare --all
```

Each branch produces these files under `dist/<branch>/`:

- `php-<upstream>-up.<revision>.tar.xz`: PHP sources with the ordered patch series.
- `php-<upstream>-up.<revision>.json`: source and patch provenance, build inputs,
  archive checksum, and verified CVE records.
- `php-<upstream>-up.<revision>.sha256`: archive and JSON sidecar checksums.

The archive includes `phpup/manifest.json`, copies of its applied patches, and
upstream license files. File ordering, ownership, timestamps, and compression are
normalized. Cached downloads are still checksum-verified. Revision `up.0` is the
unmodified PHP baseline; subsequent revisions can include compatibility or
hardening changes without constituting a verified CVE fix.

## Build Docker images

Requirements: Docker with BuildKit and the tools needed for source preparation.
Builds use a digest-pinned Debian Bookworm base and dated Debian package snapshots.
APT bootstraps CA certificates using signed Debian metadata, then uses HTTPS.

```sh
scripts/build-images.sh 8.2
python3 scripts/verify.py --branch 8.2
```

The build produces CLI, FPM, Apache + mod_php, and a matching development SDK.
Published builds target `linux/amd64`. To test locally on an ARM machine:

```sh
PLATFORM=linux/arm64 scripts/build-images.sh 8.2
PLATFORM=linux/arm64 python3 scripts/verify.py --branch 8.2
```

Local runtime tags are `phpup:<upstream>-up.<revision>-cli`, `-fpm`, and
`-apache`; a local ARM override adds `-arm64` before the variant. The SDK is
tagged with the upstream version, core/toolchain identity, and architecture.

FPM listens on port 9000, runs in the foreground, and sends logs to stderr. Its
workers use `www-data`. It speaks FastCGI and requires an HTTP frontend for web use.

The Apache variant uses the prefork MPM and mod_php, listens on port 80, serves
`/var/www/html`, and logs to stderr. Its session support is built in rather than
shared. The CLI/FPM/SDK builds keep session shared so `session.so` can be rebuilt
in isolation.

### Initial extension set

CLI/FPM images contain the standard runtime, JSON, filter, tokenizer, and
**shared session support**; the Apache image links session statically. JSON is
built in on PHP 8 and explicitly enabled on older branches. The minimal recipes
avoid pulling legacy TLS/database/image dependencies into these initial images.
Enable additional extensions through reviewed branch build options and update the
runtime dependency list and smoke tests accordingly.

The SDK also contains CGI, PHP headers, `phpize`, `php-config`, compiler tools,
Valgrind, and the matching source tree for upstream regression tests.

## Rebuild only session.so

After building the matching SDK once (CLI/FPM build; Apache uses a separate
static-session build):

```sh
scripts/build-session.sh 8.2
python3 scripts/verify.py --branch 8.2 --module
```

This runs `phpize`, configure, and make in **`ext/session` only**. It does not rebuild
Zend or the PHP executables. Output goes to `dist/<branch>/session/<architecture>/`:
`session.so`, `session.json`, and `session.sha256`. Metadata records source patches,
SDK image identity, PHP API/build information, architecture, and the module hash.

Session-only patches preserve the core/toolchain identity, allowing the existing
SDK to be reused. Changes outside `ext/session`, compiler recipes, source release,
configure options, or dependency pins require rebuilding the SDK.

Use the module only with its matching runtime and ABI. An existing PHP installation
that statically includes session cannot replace it by loading a second `session.so`;
that installation must be rebuilt/relinked. These Docker recipes deliberately use
shared session support to make the shorter rebuild path available.

## Patches and verification

Each branch's `series` file fixes patch order; its `README.md` records origin,
security attribution, and regression evidence. Patch failures, unexpected offsets,
fuzz, unsafe paths, and source checksum mismatches stop builds.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/phpup.py readme --check
python3 scripts/verify.py --all --build
```

Runtime verification makes actual FastCGI multipart requests, checks normal upload
behavior, progress cleanup, multiple serializers, and cancellation, and can load
the separately rebuilt module. Treat tests actually executed separately from CI
jobs that are merely configured.

## CI and publication

GitHub Actions validates inputs, builds the branch matrix, and uploads source,
module, and tested runtime-image artifacts. Manual runs support one branch or all.
Version-tag workflows publish the tested images to
`ghcr.io/josecarlosgarcia95/php2shell-temporal-bugfix` and attach source/module artifacts to
GitHub Releases after the matrix succeeds. A changed build input requires a new
project revision before reusing a versioned public tag.

PHP source and any derivative source patches retain the corresponding upstream
license notices. No broader license grant for unrelated project material is
implied by the upstream PHP license.
