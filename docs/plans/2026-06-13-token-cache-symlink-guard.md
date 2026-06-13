# Token Cache Symlink Guard

Status: Planned

## Problem

Token-cache reads check permissions with `os.stat` and then open the pathname,
so the checked file can differ from the opened file. Token-cache writes also
follow symbolic links, allowing a local link at the cache path to redirect the
credential write into another file.

## Plan

1. Open token-cache files with `os.open` and `O_NOFOLLOW` when the platform
   provides it.
2. Reject symbolic-link paths explicitly and keep a conservative fallback for
   platforms without `O_NOFOLLOW`.
3. Validate read permissions with `os.fstat` on the opened descriptor.
4. Preserve owner-only writes, token text format, and existing callers.
5. Add Python 2 runtime and Python 3 static mutation-sensitive coverage.
6. Run the complete repository gate and record actual verification.

## Compatibility Boundary

- Keep `access_token.string` as the default cache path and return its complete
  text contents unchanged.
- Keep created and rewritten token caches at mode 0600.
- Preserve Python 2.7 compatibility and avoid adding dependencies.
- Do not change OAuth endpoints, request signing, API-call validation, response
  bounds, or response closure behavior.

## Verification

Pending implementation.
