# Request Token Flow Test

## Status: Completed

## Context

`py-fitbit` had mocked coverage for the cached access-token path, but the
interactive no-cache OAuth flow still depended on manual testing. That branch
obtains a request token, prompts for a verifier, exchanges it for an access
token, writes `access_token.string`, and then calls the protected resource.

## Objectives

- Keep coverage Python 2-compatible and independent of live Fitbit calls.
- Stub the OAuth verifier prompt and HTTPS connection.
- Assert request-token, access-token, and protected-resource requests are built
  in order.
- Assert the newly written access-token cache remains owner-only.

## Work Completed

- Extended `tests/test_fitbit_oauth_request.py` with a mocked no-cache OAuth
  flow test.
- Improved the OAuth token test double so parsed token key/secret values flow
  through subsequent signed requests.
- Added this completed plan under `docs/plans/`.
- Updated README, VISION, and CHANGES notes for request-token flow coverage.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `make check`
- `make verify`
- `git diff --check`
