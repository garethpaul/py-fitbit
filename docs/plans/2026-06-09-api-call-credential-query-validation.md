# API Call Credential Query Validation

Status: Completed

## Context

Protected Fitbit resource calls are signed with OAuth headers. If an API path
includes query parameters such as `oauth_token`, `access_token`, or
`client_secret`, credentials can be hidden in the request URL instead of local
settings or the signed Authorization header.

## Objectives

- Reject credential-like query parameters inside protected resource API paths.
- Preserve ordinary query parameters for legitimate Fitbit resource filters.
- Keep the validation in `validate_api_call` before network connections open.
- Add Python 2 mock-based coverage for accepted non-secret queries and rejected
  credential queries.

## Work Completed

- Added a credential query-parameter denylist to `fitbit.py`.
- Extended mocked OAuth tests for non-secret query preservation and credential
  query rejection.
- Updated the Python 3 legacy safety checker and maintenance documentation.

## Verification

- `python3 scripts/check_legacy_fitbit.py`
- `python2 tests/test_fitbit_oauth_request.py`
- `make check`
- `git diff --check`
