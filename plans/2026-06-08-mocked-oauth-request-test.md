# Mocked OAuth Request Test

## Status

Completed

## Context

`py-fitbit` now has a legacy safety gate, but the Fitbit request path is still
only protected by syntax and static checks. The sample imports local
credentials, an OAuth package, and `httplib`, so tests must stub those seams and
avoid real credentials or network calls.

## Objectives

- Add a Python 2 mock-based test for the cached access-token path.
- Verify that protected resource requests are signed and sent with an OAuth
  authorization header.
- Keep the test deterministic with fake `settings`, `oauth`, and HTTPS
  connection objects.
- Run the mock test from `make verify` alongside the existing safety gate.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `make verify`
- `git diff --check`
