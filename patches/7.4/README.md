# PHP 7.4 patches

> **Corrected research (2026-10-21):** The public bundle now confirms this
> cached-pointer chain is **dead at the addref** (`Z_TRY_ADDREF(progress->data)`
> keeps the target array alive). This patch is independent hardening for stale
> counters, **not a CVE fix**. The real memory-safety issue is the serialize-state
> cross-request UAF addressed by `serializer-context-reset.patch`.


## `session-upload-progress-counters.patch`

- Category: security hardening (independent)
- Reported issues: `CVE-2026-109618`, `CVE-2026-109619` (attribution pending)
- Report: <https://jackalsyn.com/posts/php-up-2026.html>
- Affected upstream base: PHP 7.4.33

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
final `bytes_processed` value. The patched PHP 7.4.33 build reports the final
body length (`262642` in the current fixture), preserves normal upload progress and
cleanup, and passes the serializer and cancellation checks.

## `serializer-context-reset.patch`

- Category: security hardening (independent, request lifecycle)
- Reported issue: cross-request reuse of orphaned `BG(serialize)` /
  `BG(unserialize)` contexts after a pre-RINIT OOM (`CVE-2026-109618` per the
  corrected research; vendor mapping pending)
- Affected upstream base: PHP 7.4.33
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

