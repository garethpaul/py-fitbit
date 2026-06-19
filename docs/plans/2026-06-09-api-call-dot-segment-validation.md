# API Call Dot-Segment Validation

Status: Completed

## Context

Protected Fitbit resource paths were constrained to relative API paths, but
paths containing raw or percent-encoded `.` or `..` segments were still
accepted. Those paths can be normalized differently by clients, proxies, or
servers, making the requested resource less explicit than the caller-provided
string suggests.

## Objectives

- Reject raw and percent-encoded `.` and `..` segments in protected Fitbit API
  paths before any network connection opens.
- Cover the behavior with the existing Python 2 mocked OAuth request test.
- Extend the Python 3 static checker so the validation remains visible.
- Add a static `make build` alias for the legacy verification gate.
- Document the completed guard in README, SECURITY, VISION, and CHANGES.

## Work Completed

- Updated `validate_api_call` to reject decoded dot segments after trimming and
  before OAuth request creation.
- Added mocked invalid-path cases for raw and percent-encoded `/../` and `/./`
  protected resource paths.
- Extended `scripts/check_legacy_fitbit.py` to require the dot-segment guard.
- Added `make build` as a static test alias and routed `verify` through lint,
  test, build, and docs.

## Verification

- Red `make test` with dot-segment invalid-path cases.
- `make lint`
- `make test`
- `make build`
- `make docs`
- `make check`
- `git diff --check`
