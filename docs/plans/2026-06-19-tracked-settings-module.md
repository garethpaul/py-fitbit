# Tracked Settings Module

## Status: Completed

## Context

`fitbit.py` imports `settings`, but clean checkouts previously ignored the
module. PR #4 added a secret-free loader, while its standalone checker was not
connected to the canonical `make check` gate and its original plan did not meet
the repository documentation contract.

## Completed Work

1. Track `settings.py` and load the consumer key and secret only from
   `FITBIT_CONSUMER_KEY` and `FITBIT_CONSUMER_SECRET`.
2. Reject missing, empty, and whitespace-only values without printing secret
   values or opening a network connection.
3. Run the Python 2 settings contract from the existing `make check` gate.
4. Move structural settings checks into `scripts/check_legacy_fitbit.py` and
   remove the disconnected shell checker.
5. Preserve HTTPS endpoints, timeout behavior, protected-path validation,
   response-status validation, token-cache permissions, and no-network tests.

## Verification

- `make check`
- `python2 tests/test_settings.py`
- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `git diff --check`

## Remaining Limitations

The sample still requires Python 2.7 and an undeclared legacy `oauth2`
dependency. Live compatibility with Fitbit's current OAuth service is not
verified by this no-network maintenance change.
