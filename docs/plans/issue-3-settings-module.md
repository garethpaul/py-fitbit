# Issue 3: Add Tracked Settings Module

## Context

GitHub issue: `garethpaul/py-fitbit#3`

`fitbit.py` imports `settings`, but clean checkouts did not include a tracked `settings.py`, package, or example. That makes the library fail before developers can exercise runtime behavior.

## Plan

1. Add a tracked, secret-free `settings.py` module.
2. Read Fitbit OAuth credentials from `FITBIT_CONSUMER_KEY` and `FITBIT_CONSUMER_SECRET`.
3. Fail with a clear setup message when required environment variables are missing.
4. Ignore generated token files and local-only settings files.
5. Add a source-level baseline script for the expected configuration contract.

## Verification

- Run `bash scripts/check-baseline.sh`.
- Run `git diff --check`.
