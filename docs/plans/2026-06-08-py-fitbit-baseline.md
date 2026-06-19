# Py Fitbit Baseline

## Status: Completed

## Context

`py-fitbit` is a legacy Python 2 OAuth sample for Fitbit protected-resource
requests. Recent maintenance disabled debug logging by default, ignored the
local token cache, and replaced live-network behavior with mocked request-path
coverage.

## Objectives

- Preserve the historical OAuth 1 sample flow.
- Keep consumer keys, consumer secrets, and access-token cache files local.
- Verify Python 2 syntax without modernizing the sample in this pass.
- Run mocked OAuth request coverage without contacting Fitbit.
- Record the completed baseline under `docs/plans`.

## Work Completed

- Added `make check` and `make verify`.
- Added `scripts/check_legacy_fitbit.py` for local credential and debug-mode
  guardrails.
- Added a Python 2 mock-based OAuth request test for cached-token protected
  resource calls.
- Extended `make verify` to require this canonical completed plan.

## Verification

- `make check`
- `make verify`
- `python3 scripts/check_legacy_fitbit.py`
- `python2 tests/test_fitbit_oauth_request.py`
- `git diff --check`

## Follow-Up Candidates

- Document whether the demonstrated Fitbit OAuth 1 flow is still supported.
- Move token-file handling behind a helper with file-permission checks.
- Add compatibility notes before any Python 3 migration.
