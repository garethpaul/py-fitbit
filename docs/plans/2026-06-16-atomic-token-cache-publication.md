# Atomic Token Cache Publication

Status: Planned

## Context

The token-cache writer opens the live cache with `O_TRUNC` before writing the
new OAuth token. If serialization, writing, flushing, or closing fails, the
last valid cache has already been erased. Opening the destination directly can
also overwrite the target of an otherwise regular hard link.

## Objectives

- Preserve the last valid token cache when publication fails before the final
  replacement.
- Write new token material to an owner-only regular file in the destination
  directory, flush and fsync it, then publish it with one atomic rename.
- Keep existing symbolic-link, special-file, descriptor, and permission
  safeguards.
- Avoid following or modifying a hard-linked destination target during a
  successful token refresh.
- Clean only the staging file after handled failures.
- Preserve Python 2.7 compatibility, public signatures, and credential-safe
  behavior.

## Scope Boundaries

- Do not change OAuth endpoints, token serialization, API paths, dependencies,
  workflows, or the read-side cache contract.
- Do not add live Fitbit requests, credentials, or tracked bytecode.
- Do not claim durability across process termination, power loss, kernel or
  filesystem failure, or an error after the atomic replacement succeeds.

## Implementation Units

### U1. Stage token writes

- Create a temporary regular file in the selected cache directory with mode
  `0600`.
- Retain descriptor-level regular-file validation and owner-only permissions.
- Write, flush, and fsync the complete token before publication.

### U2. Publish atomically

- Recheck the destination path policy immediately before publication.
- Replace the destination with a same-directory atomic rename.
- Close descriptors and remove only the unpublished staging path after handled
  failures.

### U3. Protect behavior and evidence

- Add an executable regression that injects a staging write failure and proves
  the previous cache remains byte-for-byte intact.
- Add a hard-link regression proving publication replaces the cache directory
  entry without modifying the linked target.
- Require staging, fsync, rename, cleanup, regression, documentation, and
  completed-plan contracts in the Python 3 static checker.

## Verification

- Run the focused Python 2.7 suite and complete `make check` from the repository
  root and through the absolute Makefile path from an unrelated directory.
- Run the network-disabled, read-only, digest-pinned Python 2.7 container gate
  when the runtime is available.
- Reject hostile mutations that restore destination truncation or remove
  staging, fsync, atomic rename, failure preservation, hard-link isolation,
  cleanup, or completed evidence.
- Audit the exact diff, bytecode and temporary artifacts, credential patterns,
  conflicts, dependencies, workflows, modes, binaries, and large files.

## Risks

- Same-directory rename atomicity depends on the destination filesystem's
  ordinary POSIX rename guarantees, matching the repository's existing
  `O_NOFOLLOW`, `O_NONBLOCK`, and descriptor-oriented cache protections.
- Failures after replacement cannot restore the prior directory entry and are
  outside this change's preservation guarantee.
