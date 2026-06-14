# Make Legacy Verification Location Independent

Status: Completed

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

## Work Completed

- Added an override-protected absolute repository root to the Makefile.
- Rooted docs, Python 2 compilation, Python 3 checking, and Python 2 tests.
- Extended the legacy checker with exact Make and completed-plan contracts.

## Verification Results

- Every Make alias passed from both the repository root and an unrelated
  directory with `REPO_ROOT=/tmp` supplied on the command line.
- Full root and external `make check` runs passed in the network-disabled,
  digest-pinned Python 2.7.18 container with a read-only source mount; all 17
  mocked tests passed in each run.
- Five hostile mutations rejected removal of override protection and every
  rooted executable recipe.
- Workflow YAML parsing, exact-base protected-file comparison, secret and
  generated-artifact scans, and `git diff --check` passed.
