# PHP 8.2 patches

## `session-upload-progress-counters.patch`

- Category: security hardening (independent)
- Reported issues: `CVE-2026-109618`, `CVE-2026-109619` (attribution unconfirmed)
- Report: <https://jackalsyn.com/posts/php-up-2026.html>
- Affected upstream base: PHP 8.2.34

`php_session_rfc1867_callback()` retained `zval *` pointers to
`data["bytes_processed"]` and to the current file's `bytes_processed` bucket. The
progress array is published into the session and later separated with
`SEPARATE_ARRAY(&progress->data)`, which duplicates its HashTable. The cached bucket
addresses then refer to the previous table, so later counter writes are lost. A
request that continues after `MULTIPART_EVENT_FILE_END` exposes this without any
special allocator manipulation: the final `bytes_processed` value in the session is
stale.

The patch removes the long-lived bucket pointers. The progress structure stores the
counters as `zend_long` values and `php_session_rfc1867_sync_counters()` resolves the
exported array fields by key immediately before publishing. No HashTable bucket
address is retained across a possible array separation or replacement.

This is an independent correction, not an official PHP patch. It addresses the
demonstrated stale-pointer behavior; it does not, by itself, establish the complete
affected-version range or prove the reported exploit chain.

### Regression evidence

`tests/smoke.py --require-final-counter` sends a multipart request with two files
followed by another large form field. On unmodified PHP 8.2.34 the session's final
`bytes_processed` was `136576` for a `262642`-byte body. The patched build must
report the final body length and preserve normal progress, cleanup, serializer, and
cancellation behavior.
