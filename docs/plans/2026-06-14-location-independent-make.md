# Make Legacy Verification Location Independent

Status: Planned

## Context

The Make recipes resolve plan globs, Python sources, scripts, and tests in the
caller's current directory. Invoking the repository Makefile by absolute path
from another directory therefore does not reproduce the legacy verification
gate.

## Objectives

- Resolve the repository root from the loaded Makefile.
- Run every executable Make recipe from that root, independent of the caller.
- Protect the root derivation and all rooted recipes with mutation-sensitive
  dependency-free contracts.
- Preserve Python 2.7 behavior, Python 3 static validation, and plan coverage.

## Scope Boundaries

- Do not change Fitbit behavior, APIs, credentials, dependencies, workflow, or
  supported legacy runtime.
- Do not add live requests, generated files, or new tooling.

## Verification

- every Make alias, including `make check`, from the repository root and an
  unrelated directory
- digest-pinned Python 2.7.18 container validation
- hostile mutations covering root derivation and every rooted recipe
- workflow parsing, exact-base protected-file comparison, secret and
  generated-artifact scans, and `git diff --check`

## Work Planned

- Add an override-protected absolute repository root to the Makefile.
- Root docs, Python 2 compilation, Python 3 checking, and Python 2 tests.
- Extend the legacy checker with exact Make and completed-plan contracts.
