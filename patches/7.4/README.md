# PHP 7.4 patches

## `official-early-rinit-backport.patch`

- Category: official-derived security backport (partial)
- Official fix: PHP 8.2.35 "Avoid state corruption via bailout"
- CVE addressed: CVE-2026-109619 (RCE via stale global state)
- Affected upstream base: PHP 7.4.33 (EOL)
- Source commit: `01a40e89fbfc499936e3b05888d8f00bfde886df`

This backports the early request reset from the official fix:
`php_basic_early_rinit()` resets `BG(serialize)`, `BG(unserialize)` and the URL
scanner state before `php_hash_environment()`, and the session upload-progress
callback initializes its globals early and refuses to run after RINIT.

### Scope and limitations

This is **not** a complete backport of the official fix. It does not include the
Zend allocator/OOM state redesign for CVE-2026-109618, nor the
`incomplete_classes_only` serializer mode. It must be treated as EOL hardening for
the stale-global-state issue, not as equivalent to PHP 8.2.35. The local image is
not an official security release.

### Verification

`tests/smoke.py` exercises CLI/FPM upload progress, cleanup, serializers and
cancellation; `tests/apache_smoke.py` checks the Apache/mod_php variant over HTTP.
The backport does not change the normal session paths covered by those tests.
