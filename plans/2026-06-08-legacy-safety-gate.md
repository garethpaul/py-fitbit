# Legacy Safety Gate

## Status

Completed

## Context

`py-fitbit` is a Python 2 OAuth sample with local credential settings and a
local access-token cache. The repository had no validation command, debug
logging was enabled by default, and the generated token cache file was not
ignored.

## Objectives

- Add a local verification command that does not contact Fitbit.
- Compile-check the legacy Python 2 source.
- Ensure local credential and token files remain ignored.
- Keep debug logging disabled by default.

## Verification

- `make verify`
- `python3 scripts/check_legacy_fitbit.py`
- `git diff --check`

## Follow-Up Candidates

- Move token storage behind a small helper with file-permission checks.
- Document whether the demonstrated Fitbit OAuth 1 flow is still supported.
