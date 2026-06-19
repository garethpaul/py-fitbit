# API Call Fragment Validation

Status: Completed

## Context

`fitbit(api_call)` signs and sends protected Fitbit resource paths. Existing
guards rejected absolute URLs, scheme-relative URLs, and raw whitespace before
opening network connections, but paths with URL fragments could still pass
through the OAuth request path. Fragments are not sent to servers, but they can
hide local-only notes or token-like strings in call sites.

## Objectives

- Reject `api_call` values containing `#` fragments.
- Keep valid Fitbit API paths and query strings unchanged.
- Add mocked Python 2 coverage that proves fragmented paths fail before network
  connections are opened.
- Document the fragment guard in README, VISION, SECURITY, and CHANGES.

## Work Completed

- Added fragment rejection to `validate_api_call`.
- Added a fragmented protected-resource path to the invalid path test table.
- Extended `scripts/check_legacy_fitbit.py` to preserve the fragment guard.
- Added this completed plan under `docs/plans/`.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `git diff --check`
