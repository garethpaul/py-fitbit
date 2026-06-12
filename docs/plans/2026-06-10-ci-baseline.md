# Py Fitbit CI Baseline

## Status: Completed

## Context

`py-fitbit` has a local `make check` baseline for the legacy OAuth sample and
requires Python 2 for syntax and mocked OAuth tests. Hosted validation must run
that full contract rather than silently skipping the legacy behavior.

## Objectives

- Run the existing repository baseline in GitHub Actions.
- Run Python 2 syntax and mocked OAuth tests on every hosted validation.
- Pin the legacy runtime container and checkout action by digest/commit.
- Disable checkout credential persistence and keep permissions read-only.
- Make the CI workflow presence part of the checked repository contract.

## Work Completed

- Added `.github/workflows/check.yml` to run `make check` on pushes, pull
  requests, and manual dispatches.
- Added a digest-pinned Python 2.7.18 container running the complete gate.
- Added CODEOWNERS and checker enforcement for the sole hosted workflow.
- Extended `scripts/check_legacy_fitbit.py` to require the CI workflow and this
  completed plan.
- Updated README, VISION, SECURITY, and CHANGES with the CI baseline.

## Verification

- `make check`
- `python3 scripts/check_legacy_fitbit.py`
- five hostile workflow and ownership mutations
- `git diff --check`
