# PHP 5.6 patches

No independent patch is applied for the reported upload-progress counter issue.
PHP 5.6 stores the counters in standalone zvals and publishes the progress root
array with reference count 2. It does not retain HashTable bucket pointers, so the
stale-bucket defect demonstrated on PHP 7/8 is not reproducible here. Reassess if
the official advisory identifies a PHP 5.6-specific issue.
