# PHP 7.2 patches

## `official-early-rinit-backport.patch`

- Category: official-derived security backport (partial)
- Official fix: PHP 8.2.35 "Avoid state corruption via bailout"
- CVE addressed: CVE-2026-109619 (RCE via stale global state)
- Affected upstream base: PHP 7.2.34 (EOL)
- Source commit: `01a40e89fbfc499936e3b05888d8f00bfde886df`

Backports the early request reset: `php_basic_early_rinit()` clears
`BG(serialize)`, `BG(unserialize)` and the URL scanner state before
`php_hash_environment()`, and the upload-progress callback initializes its globals
early and refuses to run after RINIT.

### Scope and limitations

This is **not** a complete backport. It does not include the Zend allocator/OOM
state redesign for CVE-2026-109618 or the `incomplete_classes_only` serializer
mode. Treat the image as EOL hardening for the stale-global-state issue, not as
equivalent to an official security release.

### Verification

`tests/smoke.py` covers CLI/FPM upload progress, cleanup, serializers and
cancellation; `tests/apache_smoke.py` checks the Apache/mod_php variant over HTTP.
