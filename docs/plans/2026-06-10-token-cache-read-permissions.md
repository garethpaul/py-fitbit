# Token Cache Read Permissions

## Status: Completed

## Context

`py-fitbit` writes `access_token.string` with owner-only permissions, but the
cached-token branch still trusted a pre-existing token cache created outside
the helper. On shared machines, a group-readable or world-readable cache can
expose OAuth credentials before the sample ever reaches Fitbit.

## Objectives

- Reject existing `access_token.string` files with group or other permissions.
- Fail before the cached-token branch opens a Fitbit network connection.
- Preserve the request-token branch and owner-only token-cache writer.
- Cover the behavior with the existing Python 2 mocked test harness.

## Work Completed

- Added a read-time permission check in `read_access_token_string`.
- Delayed cached-token HTTPS connection creation until after the token cache is
  accepted.
- Updated cached-token tests to use the owner-only writer helper.
- Added mocked coverage for rejecting a readable token cache before networking.
- Extended the Python 3 safety checker and maintenance documentation.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `make verify`
- `git diff --check`
