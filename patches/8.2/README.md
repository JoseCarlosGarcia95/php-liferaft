# PHP 8.2 patches

> **Corrected research (2026-10-21):** The public bundle now confirms this
> cached-pointer chain is **dead at the addref** (`Z_TRY_ADDREF(progress->data)`
> keeps the target array alive). This patch is independent hardening for stale
> counters, **not a CVE fix**. The real memory-safety issue is the serialize-state
> cross-request UAF addressed by `serializer-context-reset.patch`.


## `session-upload-progress-counters.patch`

- Category: security hardening (independent)
- Reported issues: `CVE-2026-109618`, `CVE-2026-109619` (attribution pending)
- Report: <https://jackalsyn.com/posts/php-up-2026.html>
- Affected upstream base: PHP 8.2.34

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
final `bytes_processed` value. The patched PHP 8.2.34 build reports the final
body length (`262642` in the current fixture), preserves normal upload progress and
cleanup, and passes the serializer and cancellation checks.

## `serializer-context-reset.patch`

- Category: security hardening (independent, request lifecycle)
- Reported issue: orphaned `BG(serialize)` / `BG(unserialize)` contexts after a
  pre-RINIT OOM (stage map supplied by the owner; no public follow-up yet)
- Affected upstream base: PHP 8.2.34
- Relationship to the counter patch: independent root cause; neither patch fixes
  the other

If a request aborts with an OOM while `php_var_serialize()` or
`php_var_unserialize()` is active, the request-global serializer context remains
with `level=1` and `data` pointing at request memory. Later request startup parses
multipart data in `php_hash_environment()` **before** `zend_activate_modules()`
(RINIT). With `session.upload_progress` enabled and a `PHPSESSID` field, that
pre-RINIT parse serializes session progress and reuses the stale context.

The patch resets `BG(serialize)`, `BG(unserialize)`, and `serialize_lock` at the
start of `php_request_startup()`, immediately before `php_hash_environment()`.
It does not free the old pointer, because that memory belongs to the previous
request and may already be freed; it only prevents any reuse. The normal RINIT
reset remains as a second guard.

This is an independent correction, not an official PHP patch. It blocks the
demonstrated cross-request reuse; it does not establish the complete affected
range or prove the reported RCE chain.

### Regression evidence

A local debug harness primes an orphaned context with an OOM inside `serialize()`,
triggers a pre-RINIT OOM with a large multipart filename and `PHPSESSID`, then
sends a second multipart. Before the patch the second request logs
`SER_INIT level=1 data=<stale pointer>` before RINIT; after the patch it logs
`RINIT_BEFORE ser=0` and a fresh `SER_INIT level=0`, while normal sessions and
serialization continue to work.

### ASAN A/B evidence (lab)

An ASAN build of the unmodified PHP 8.2.34 sources (`USE_ZEND_ALLOC=0`,
`max_allocation_size_mb=4`) reproduces the cross-request reuse deterministically:

- R1 seeds a ~3.95 MB session, then OOM-aborts inside the session encode
  (`smart_str` growth) during the pre-RINIT multipart parse, leaving
  `BG(serialize).level = 1` with `data` pointing at the request's
  `php_serialize_data`.
- R2, the first request afterwards on the same worker, reuses that context in
  `ps_srlzr_encode_php_serialize()` while still inside `php_hash_environment()`.

Without this patch the R2 request dies with:

```text
ERROR: AddressSanitizer: heap-use-after-free ... READ of size 4
    #0 php_add_var_hash              ext/standard/var.c:669
    #1 php_var_serialize_intern      ext/standard/var.c:1006
    #3 ps_srlzr_encode_php_serialize ext/session/session.c:855
    ...
   #14 php_hash_environment / php_request_startup   (pre-RINIT)
allocated by: php_var_serialize_init var.c:1284 (R1, session encode)
```

(`var.c:669` is PHP 8.2.34's location of the `data->n += 1` access that the
corrected research reports as `var.c:756` on 8.4.4.)

With this patch applied to the identical build, the identical R1/R2 sequence
returns HTTP 200 for R2 and raises no ASAN error: the reset clears the stale
context before `php_hash_environment()` can serialize through it.

The deterministic OOM placement and the between-requests free are lab-only
harness aids that emulate the production Zend allocator (`memory_limit` OOM
bailout and request sweep). The fix patch itself contains none of them.
