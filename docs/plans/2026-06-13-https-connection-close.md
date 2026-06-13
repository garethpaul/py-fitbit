# HTTPS Connection Close Contract

Status: Completed

## Problem

The legacy client now closes every Fitbit response object, but each call leaves
its shared `HTTPSConnection` open after the OAuth and protected-resource
sequence. Intermediate token, status, body-size, parsing, prompt, and cache
errors can also exit without releasing the connection.

## Plan

1. Keep one connection available across the request-token, access-token, and
   protected-resource requests.
2. Close that connection exactly once when `fitbit()` exits after a connection
   has been created, on success and failure paths.
3. Preserve validation-before-network behavior, OAuth signing and prompts,
   response closure, token-cache handling, and returned body bytes.
4. Add mocked Python 2 regressions for cached-token success, interactive-token
   success, and an HTTP failure after connection creation.
5. Add mutation-sensitive static contracts and synchronized maintenance docs.
6. Run the complete host and digest-pinned Python 2.7.18 repository gates and
   record actual verification.

## Compatibility Boundary

- Do not close the connection between OAuth exchanges or before the protected
  resource request completes.
- Do not change public function signatures, endpoints, headers, token formats,
  response bounds, status precedence, or cache permissions.
- Preserve Python 2.7 compatibility and add no dependencies.
- Do not make live Fitbit requests or require credentials.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make lint`, `make test`, `make build`, `make verify`, and `make check`
- digest-pinned Python 2.7.18 container `make check`
- hostile mutations covering close placement, exactly-once behavior, success,
  failure, documentation, completed status, and evidence
- workflow parse, secret and generated-artifact scans, and `git diff --check`

## Work Completed

- Wrapped the complete network portion of `fitbit()` in a `try`/`finally` that
  closes the created shared HTTPS connection exactly once.
- Preserved one connection across request-token, access-token, and protected
  resource requests and preserved validation-before-network behavior.
- Added close tracking and exactly-once assertions for cached-token success,
  interactive-token success, OAuth HTTP failure, and protected-resource HTTP
  failure.
- Added static implementation/test contracts and synchronized maintenance,
  security, vision, and change-log guidance.

## Verification Results

- `python2 tests/test_fitbit_oauth_request.py` passed all 17 mocked tests.
- Canonical `make check` passed on the host and in the network-disabled,
  digest-pinned Python 2.7.18 container with a read-only source mount.
- Eight hostile mutations covering runtime close removal, both success paths,
  both HTTP failure paths, documentation, and completed plan status were
  rejected, including a separate exact-evidence mutation.
- Workflow YAML parsing, exact-base protected-file comparison, added-line
  secret scanning, generated-artifact scanning, and `git diff --check` passed.
