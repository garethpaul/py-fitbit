# API Call Whitespace Validation

## Status: Completed

## Context

Protected Fitbit resource calls are passed to the legacy sample as API paths.
The existing guard rejected absolute URLs and scheme-relative URLs before any
network connection opened, but raw whitespace inside a path could still reach
`httplib`.

## Goals

- Continue trimming leading and trailing whitespace for legacy call sites.
- Reject embedded whitespace or control characters inside protected resource
  API paths.
- Cover malformed whitespace paths with the mocked OAuth tests.
- Extend the repository-local safety checker so the guard cannot be removed
  silently.

## Work Completed

- Updated `validate_api_call` to reject paths containing raw whitespace after
  trimming.
- Added mocked invalid-path coverage for a path with a space and a path with a
  newline.
- Updated `scripts/check_legacy_fitbit.py`, README, VISION, SECURITY, and
  CHANGES notes for the whitespace guard.

## Verification

- `python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"`
- `python3 scripts/check_legacy_fitbit.py`
- `python2 tests/test_fitbit_oauth_request.py`
- `make check`
- `git diff --check`
