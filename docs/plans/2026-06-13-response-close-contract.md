---
title: Response Close Contract
type: fix
status: completed
date: 2026-06-13
---

# Response Close Contract

Status: Completed

## Context

The shared Fitbit response reader bounds successful bodies and rejects non-2xx
statuses, but it never explicitly closes the `HTTPResponse`. OAuth token and
protected-resource responses can therefore retain connection resources until
garbage collection, including on read, status, and size failures.

## Priority

Deterministic response cleanup is a small reliability improvement with a clear
test boundary. It prevents later changes from leaking response resources while
keeping the legacy Python 2 OAuth behavior and shared HTTPS connection intact.

## Objectives

- Close every non-null Fitbit `HTTPResponse` after the bounded read attempt.
- Close responses on success, non-2xx, oversized-body, and read-error paths.
- Preserve current status errors, the 1 MiB body cap, and returned body bytes.
- Keep the shared `HTTPSConnection` available across the OAuth token exchange.
- Protect implementation, regression tests, documentation, and completed plan
  in the repository-local fail-closed checker.

## Implementation Units

### 1. Shared response lifecycle

Files:

- `fitbit.py`
- `tests/test_fitbit_oauth_request.py`

Requirements:

- Put the existing bounded read and validation logic inside `try`/`finally`.
- Call `response.close()` exactly once after every attempted response read.
- Add deterministic close tracking and a synthetic read failure.
- Do not close the `HTTPSConnection` between OAuth requests.

### 2. Contracts and documentation

Files:

- `scripts/check_legacy_fitbit.py`
- `README.md`
- `SECURITY.md`
- `VISION.md`
- `CHANGES.md`
- `docs/plans/2026-06-13-response-close-contract.md`

Requirements:

- Document explicit response-object cleanup.
- Require the close implementation and lifecycle regression names.
- Record completed status and actual verification only after implementation
  and tests pass.

## Test Scenarios

- An exact-limit successful response returns its body and is closed.
- A non-2xx response keeps the existing status error and is closed.
- An oversized response keeps the existing bounded-body error and is closed.
- A response read exception propagates and the response is still closed.
- Existing OAuth request, credential-output, cache-permission, URL-validation,
  response-size, and hosted-baseline tests remain green.

## Scope Boundaries

- Do not change OAuth endpoints, signatures, prompts, or token parsing.
- Do not change response status precedence or the body-size limit.
- Do not add dependencies or raise the Python 2.7 compatibility floor.
- Do not make live Fitbit calls or require credentials.

## Verification

- `python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make lint`
- `make test`
- `make build`
- `make verify`
- `make check`
- digest-pinned Python 2.7.18 container `make check`
- workflow YAML parse
- `git diff --check`

## Work Completed

- Wrapped the existing bounded response read and validation logic in
  `try`/`finally` and close each attempted response exactly once.
- Added deterministic response instances, close counts, and a synthetic read
  failure to the mocked Python 2 suite.
- Protected the response-close implementation, tests, documentation, and this
  completed plan in the fail-closed repository checker.

## Verification Results

Completed locally on 2026-06-13:

- `python2 tests/test_fitbit_oauth_request.py` (16 tests passed)
- `python3 scripts/check_legacy_fitbit.py`
- `make lint`
- `make test`
- `make build`
- `make verify`
- `make check`
- network-isolated digest-pinned Python 2.7.18 container `make check`
- workflow YAML parse
- six hostile cleanup-contract mutations rejected
- `git diff --check`
