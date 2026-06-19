# Fitbit HTTP Status Validation

Status: Completed

## Context

The legacy OAuth helper read and returned every HTTP response body without
checking its status. A Fitbit error page could therefore be parsed as an OAuth
token or returned to a caller as if a protected resource request succeeded.
Including failed response bodies in errors would also risk leaking credential
or health-data details into logs.

## Objectives

- Reject non-2xx OAuth request-token and access-token responses.
- Reject non-2xx protected resource responses.
- Drain response bodies without including them in exceptions.
- Cover both paths with mocked Python 2 tests and no live Fitbit requests.

## Work Completed

- Added `read_success_response` as the shared response body and status gate.
- Routed OAuth exchanges and protected resource calls through the shared gate.
- Added mocked 503 token-response and 401 protected-resource regressions.
- Extended the Python 3 safety checker and maintenance documentation.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- Bypassed the protected-resource status reader in a mutation check and
  confirmed the safety gate rejected the change.
- `git diff --check`
