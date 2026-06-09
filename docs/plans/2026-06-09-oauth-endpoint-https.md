# OAuth Endpoint HTTPS Guard

## Status: Completed

## Context

The legacy Fitbit OAuth sample used `http://api.fitbit.com` constants for the
request-token, access-token, and authorization endpoints. The request path was
already mocked in tests, but the constants themselves were not covered.

## Goals

- Pin OAuth request, access-token, and authorization endpoint constants to
  `https://api.fitbit.com`.
- Cover the endpoint constants in the Python 2 mocked regression test.
- Add a Python 3 repository safety check so HTTP OAuth endpoints do not return.
- Document the HTTPS endpoint guard in README, VISION, and CHANGES.

## Work Completed

- Updated `fitbit.py` OAuth endpoint constants to HTTPS.
- Added `test_oauth_endpoints_use_https` to the Python 2 test suite.
- Extended `scripts/check_legacy_fitbit.py` to reject HTTP OAuth endpoint
  constants.
- Added this completed plan under `docs/plans/`.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `make verify`
- `git diff --check`
