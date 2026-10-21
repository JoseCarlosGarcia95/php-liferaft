# php-liferaft

Inspectable PHP security backports, source archives, and Docker CLI/FPM builds.
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
| 8.2 | 8.2.34 | [patches/8.2](patches/8.2) |
| 8.3 | 8.3.35 | [patches/8.3](patches/8.3) |
| 8.4 | 8.4.26 | [patches/8.4](patches/8.4) |
| 8.5 | 8.5.11 | [patches/8.5](patches/8.5) |

## Fixed CVEs

The table is generated from [`security.json`](security.json). Each claim identifies
one branch, its first fixed project revision, the applied patches, and regression
references. Rows marked `independent` are source-analysis corrections, not official
PHP patches. For these two identifiers, the mapping comes from the linked report
until PHP publishes its advisory.

<!-- phpup:fixed-cves:start -->

| CVE | Branch | First fixed build | Patches | Regression | Origin |
| --- | --- | --- | --- | --- | --- |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 7.0 | 7.0.33-up.1 | [session-upload-progress-counters.patch](patches/7.0/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 7.1 | 7.1.33-up.1 | [session-upload-progress-counters.patch](patches/7.1/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 7.2 | 7.2.34-up.1 | [session-upload-progress-counters.patch](patches/7.2/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 7.3 | 7.3.33-up.1 | [session-upload-progress-counters.patch](patches/7.3/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 7.4 | 7.4.33-up.1 | [session-upload-progress-counters.patch](patches/7.4/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.0 | 8.0.30-up.1 | [session-upload-progress-counters.patch](patches/8.0/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.1 | 8.1.34-up.1 | [session-upload-progress-counters.patch](patches/8.1/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.2 | 8.2.34-up.1 | [session-upload-progress-counters.patch](patches/8.2/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.3 | 8.3.35-up.1 | [session-upload-progress-counters.patch](patches/8.3/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.4 | 8.4.26-up.1 | [session-upload-progress-counters.patch](patches/8.4/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109618](https://jackalsyn.com/posts/php-up-2026.html) | 8.5 | 8.5.11-up.1 | [session-upload-progress-counters.patch](patches/8.5/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 7.0 | 7.0.33-up.1 | [session-upload-progress-counters.patch](patches/7.0/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 7.1 | 7.1.33-up.1 | [session-upload-progress-counters.patch](patches/7.1/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 7.2 | 7.2.34-up.1 | [session-upload-progress-counters.patch](patches/7.2/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 7.3 | 7.3.33-up.1 | [session-upload-progress-counters.patch](patches/7.3/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 7.4 | 7.4.33-up.1 | [session-upload-progress-counters.patch](patches/7.4/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.0 | 8.0.30-up.1 | [session-upload-progress-counters.patch](patches/8.0/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.1 | 8.1.34-up.1 | [session-upload-progress-counters.patch](patches/8.1/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.2 | 8.2.34-up.1 | [session-upload-progress-counters.patch](patches/8.2/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.3 | 8.3.35-up.1 | [session-upload-progress-counters.patch](patches/8.3/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.4 | 8.4.26-up.1 | [session-upload-progress-counters.patch](patches/8.4/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |
| [CVE-2026-109619](https://jackalsyn.com/posts/php-up-2026.html) | 8.5 | 8.5.11-up.1 | [session-upload-progress-counters.patch](patches/8.5/session-upload-progress-counters.patch) | [smoke.py](tests/smoke.py), [upload.php](tests/fixtures/upload.php) | independent |

<!-- phpup:fixed-cves:end -->

### Reported upload-progress issues

The [third-party report](https://jackalsyn.com/posts/php-up-2026.html) attributes
cached-counter lifetime issues in `ext/session` to `CVE-2026-109618` and
`CVE-2026-109619`. The table above records independent corrections for PHP 7.0
through 8.5. Their official attribution remains under investigation, and the
entries do not claim coverage for PHP 5.6 or for unrelated code paths.

The checked PHP 8.2.34 source retains a reference to the progress root array before
publishing it into session data. PHP 5.6 uses a different zval layout. The presence
of cached pointers by itself does not establish the article's claimed default-
configuration use-after-free or remote-code-execution chain.

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

The build produces CLI, FPM, and a matching development SDK. Published builds target
`linux/amd64`. To test locally on an ARM machine:

```sh
PLATFORM=linux/arm64 scripts/build-images.sh 8.2
python3 scripts/verify.py --branch 8.2 --platform linux/arm64
```

Local runtime tags are `phpup:<upstream>-up.<revision>-cli` and `-fpm`; a local ARM
override adds `-arm64` before the variant. Exact image names are recorded in
`dist/<branch>/images-<architecture>.json`. The SDK is tagged with the upstream
version, core/toolchain identity, and architecture.

FPM listens on port 9000, runs in the foreground, and sends logs to stderr. Its
workers use `www-data`. It speaks FastCGI and requires an HTTP frontend for web use.

### Initial extension set

Images contain the standard runtime, JSON, filter, tokenizer, and **shared session
support**. JSON is built in on PHP 8 and explicitly enabled on older branches.
The minimal recipes avoid pulling legacy TLS/database/image dependencies into
these initial images. Enable additional extensions through reviewed branch build
options and update the runtime dependency list and smoke tests accordingly.

The SDK also contains CGI, PHP headers, `phpize`, `php-config`, compiler tools,
Valgrind, and the matching source tree for upstream regression tests.

## Rebuild only session.so

After building the matching SDK once:

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
`ghcr.io/josecarlosgarcia95/php-liferaft` and attach source/module artifacts to
GitHub Releases after the matrix succeeds. A changed build input requires a new
project revision before reusing a versioned public tag.

PHP source and any derivative source patches retain the corresponding upstream
license notices. No broader license grant for unrelated project material is
implied by the upstream PHP license.
