# PHP 7.1 patches

> **Official advisory (2026-10-21):** CVE-2026-109618 is an OOM-corruption
> RCE and CVE-2026-109619 is an RCE via stale global state. This EOL backport is
> independent hardening, not a complete official-equivalent fix. Official patched
> releases exist only for PHP 8.2.35, 8.3.36, 8.4.27 and 8.5.12.


## `session-upload-progress-counters.patch`

- Category: security hardening (independent)
- Reported issues: `CVE-2026-109618`, `CVE-2026-109619` (attribution pending)
- Report: <https://jackalsyn.com/posts/php-up-2026.html>
- Affected upstream base: PHP 7.1.33

`php_session_rfc1867_callback()` retained `zval *` pointers to
`data["bytes_processed"]` and to the current file's `bytes_processed` bucket. The
progress array is published into the session and later separated with
`SEPARATE_ARRAY(&progress->data)`, which duplicates its HashTable. The cached bucket
addresses then refer to the previous table, so later counter writes are lost. A
request that continues after `MULTIPART_EVENT_FILE_END` exposes this without any
allocator manipulation: the final `bytes_processed` value in the session is stale.

The patch removes the long-lived bucket pointers. The progress structure stores the
counters as `zend_long` values and `php_session_rfc1867_sync_counters()` resolves the
exported array fields by key immediately before publishing. No HashTable bucket
address is retained across a possible array separation or replacement.

This is an independent correction, not an official PHP patch. It addresses the
demonstrated stale-pointer behavior; it does not, by itself, establish the complete
affected-version range or prove the reported exploit chain.

### Regression evidence

`tests/smoke.py --require-final-counter` sends a multipart request with two files
followed by another large form field. Unmodified modern branches report a stale
final `bytes_processed` value. The patched PHP 7.1.33 build reports the final
body length (`262642` in the current fixture), preserves normal upload progress and
cleanup, and passes the serializer and cancellation checks.

## `serializer-context-reset.patch`

- Category: security hardening (independent, request lifecycle)
- Reported issue: CVE-2026-109619, RCE via stale global state (official
  advisory); this EOL backport is independent hardening
- Affected upstream base: PHP 7.1.33
- Relationship to the counter patch: independent root cause; neither patch fixes
  the other

The official advisory identifies CVE-2026-109619 as an RCE via stale global
state: an OOM can leave request-owned serializer globals pointing at freed
memory, and a later request on the same worker can reuse them before normal
initialization. This EOL backport applies the early reset only; it is not the
full official allocator/session fix.

The patch resets `BG(serialize)`, `BG(unserialize)`, and `serialize_lock` at the
start of `php_request_startup()`, immediately before `php_hash_environment()`.
It does not free the old pointer, because that memory belongs to the previous
request and may already be freed; it only prevents reuse. The normal RINIT
reset remains as a second guard.

This is an independent EOL backport, not an official PHP patch. Official
patched releases exist for PHP 8.2.35, 8.3.36, 8.4.27 and 8.5.12 only.

### Regression evidence

A local debug harness primes an orphaned context with an OOM inside `serialize()`,
triggers a pre-RINIT OOM with a large multipart filename and `PHPSESSID`, then
sends a second multipart. Before the patch the second request logs
`SER_INIT level=1 data=<stale pointer>` before RINIT; after the patch it logs
`RINIT_BEFORE ser=0` and a fresh `SER_INIT level=0`, while normal sessions and
serialization continue to work.

