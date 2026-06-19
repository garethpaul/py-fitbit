# Token Cache Permissions

## Status: Completed

## Context

`py-fitbit` stores the OAuth access token cache in `access_token.string`. The
file is ignored by git, but the legacy sample wrote it with the process default
umask. On shared machines that can accidentally leave health-data credentials
readable by other local users.

## Objectives

- Preserve the legacy Python 2 OAuth flow.
- Keep `access_token.string` untracked and local.
- Write the access-token cache with owner-only permissions.
- Add mocked test coverage for token-cache read/write behavior.
- Make docs plan verification cover every completed plan under `docs/plans`.

## Work Completed

- Added Python 2-compatible token cache read/write helpers.
- Wrote `access_token.string` through `os.open` with `0600` permissions.
- Added mocked test coverage for token-cache mode and content.
- Extended the legacy safety checker to require token-cache helpers.
- Updated README, VISION, CHANGES, and the docs verification target.

## Verification

- `python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"`
- `python3 scripts/check_legacy_fitbit.py`
- `python2 tests/test_fitbit_oauth_request.py`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Return structured errors instead of printing or exiting inside the library
  path.
- Document whether the demonstrated Fitbit OAuth 1 flow is still supported by
  current Fitbit APIs.
