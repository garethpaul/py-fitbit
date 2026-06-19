# API Call Path Validation

## Status: Completed

## Context

`fitbit.fitbit(api_call)` accepted the protected resource target directly and
passed it into both OAuth signing and `HTTPSConnection.request`. The sample is
intended to call Fitbit on the fixed `api.fitbit.com` host, so callers should
provide Fitbit API paths rather than absolute URLs or scheme-relative targets.

## Objectives

- Validate protected resource targets before opening a network connection.
- Preserve Python 2 compatibility for the legacy sample.
- Keep whitespace-trimmed API paths working for caller convenience.
- Cover rejected targets with mocks so no invalid input can create an OAuth
  request or HTTPS connection.

## Work Completed

- Added `validate_api_call` to require a Fitbit API path, trim valid paths, and
  reject absolute or scheme-relative URLs.
- Called the validator before creating the HTTPS connection in `fitbit.fitbit`.
- Extended mocked OAuth tests for trimmed paths and rejected non-API targets.
- Updated the legacy safety checker and repository documentation for the path
  guard.

## Verification

- `python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"`
- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `make verify`
- `git diff --check`
