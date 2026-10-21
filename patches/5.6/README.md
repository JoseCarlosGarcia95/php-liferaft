# PHP 5.6 patches

No independent patch is applied for the reported upload-progress counter issue.
PHP 5.6 stores the counters in standalone zvals and publishes the progress root
array with reference count 2. It does not retain HashTable bucket pointers, so the
stale-bucket defect demonstrated on PHP 7/8 is not reproducible here. Reassess if
the official advisory identifies a PHP 5.6-specific issue.

## `serializer-context-reset.patch`

- Category: security hardening (independent, request lifecycle)
- Reported issue: cross-request reuse of orphaned `BG(serialize)` /
  `BG(unserialize)` contexts after a pre-RINIT OOM (`CVE-2026-109618` per the
  corrected research; vendor mapping pending)
- Affected upstream base: PHP 5.6.40
- Relationship to the counter patch: independent root cause; neither patch fixes
  the other

The corrected analysis of the public bundle identifies the real memory-safety
issue as a serialize-state cross-request UAF: an OOM aborts request startup after
`PHP_VAR_SERIALIZE_INIT` but before its matching destroy, leaving
`BG(serialize).level > 0` with `data` pointing at request memory. On a prefork
SAPI the child survives; the next request reuses the dangling context in
`php_add_var_hash()` (`var.c`, `data->n += 1`) before the normal RINIT reset.

The patch resets `BG(serialize)`, `BG(unserialize)`, and `serialize_lock` at the
start of `php_request_startup()`, immediately before `php_hash_environment()`.
It does not free the old pointer, because that memory belongs to the previous
request and may already be freed; it only prevents reuse. The normal RINIT
reset remains as a second guard.

This is an independent correction, not an official PHP patch. It blocks the
demonstrated cross-request reuse; the corrected research rates the impact as a
memory-safety bug (not RCE), and vendor CVE mapping remains pending.

### Regression evidence

A local debug harness primes an orphaned context with an OOM inside `serialize()`,
triggers a pre-RINIT OOM with a large multipart filename and `PHPSESSID`, then
sends a second multipart. Before the patch the second request logs
`SER_INIT level=1 data=<stale pointer>` before RINIT; after the patch it logs
`RINIT_BEFORE ser=0` and a fresh `SER_INIT level=0`, while normal sessions and
serialization continue to work.

