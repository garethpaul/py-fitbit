# Changes

## 2026-06-26 13:33 PDT - P2 - Validate encoded JSON resource responses

### Summary

Closed a response-validation gap where encoded `.json` resource paths could
return malformed JSON without raising the privacy-safe structured error.

### Work completed

- Added bounded percent-decoding when classifying protected-resource paths for
  JSON response validation.
- Preserved the exact path used for OAuth signing and the HTTPS request.
- Added a red-first regression test and a hostile checker-integrity mutation.
- JSON response validation follows bounded percent-decoding of the protected-resource path without rewriting the signed request target.

### Threads

- Started: none — the defect was reproduced and fixed directly.
- Continued: none.
- Stopped: none.

### Files changed

- `fitbit.py` — classifies encoded JSON paths without rewriting them.
- `tests/test_fitbit_oauth_request.py` — verifies malformed encoded JSON fails
  while the signed and transmitted target remains unchanged.
- `scripts/check_legacy_fitbit.py` and `tests/test_checker_integrity.py` — bind
  the source, test, documentation, and hostile-mutation contracts.
- `README.md`, `SECURITY.md`, `VISION.md`, and
  `docs/plans/2026-06-26-encoded-json-response-validation.md` — record scope,
  compatibility, and verification evidence.

### Validation

- Red-first Python 3 regression test — failed because malformed JSON on
  `/1/user/-/profile%2Ejson` did not raise `FitbitResponseError`.
- Focused Python 3 mocked OAuth suite — 38 tests passed after implementation.
- Complete digest-pinned, network-disabled Python 2.7.18 `make check` — Python
  2 and Python 3 OAuth suites passed 38 tests each, settings suites passed 12
  tests each, checker integrity passed 4 tests, and all 49 Make authority cases
  passed.
- `git diff --check` passed; exact-head review and hosted verification remain
  the next actions.
- Hosted Python 2.7 verification and CodeQL passed on PR #20.
- `$codex-review` was invoked against `origin/master` but OpenAI authentication
  returned HTTP 401 before analysis; an immutable manual review of the matching
  local and PR head found no actionable issue.

### Bugs / findings

- P2: encoded `.json` paths bypassed malformed-JSON response validation even
  though Fitbit receives the decoded resource extension.

### Blockers

- Host Python 2 is unavailable; the digest-pinned Python 2.7.18 container is
  authoritative for legacy execution.
- The Codex review helper cannot authenticate to the OpenAI API in this
  environment; no model finding was produced or silently ignored.

### Next action

- Re-run exact-head gates after this evidence-only amendment and merge only the
  reviewed hosted-green head.

## 2026-06-26 02:43 PDT - P2 - Structure Fitbit response failures

### Summary

Replaced string-only response failures with a backward-compatible structured
exception while preserving privacy-safe messages, cleanup, and transport error
behavior.

### Work completed

- Added `FitbitResponseError(IOError)` with stable `operation`, `reason`,
  `status`, and `limit` fields.
- Applied structured reasons to non-2xx, oversized-body, and invalid-JSON
  failures without storing or parsing provider error bodies.
- Extended the mocked Python 2/3 suite across OAuth and protected-resource
  failures and added a hostile checker-integrity mutation.
- Retired the completed structured-error roadmap item without inventing new
  work.

### Threads

- Started: none — implementation and verification were completed directly.
- Continued: none.
- Stopped: none.

### Files changed

- `fitbit.py` — defines and raises the structured response exception.
- `tests/test_fitbit_oauth_request.py` — verifies fields and compatibility.
- `scripts/check_legacy_fitbit.py` and `tests/test_checker_integrity.py` — bind
  runtime, test, documentation, roadmap, and plan contracts.
- `README.md`, `SECURITY.md`, `VISION.md`, and
  `docs/plans/2026-06-26-structured-fitbit-response-errors.md` — document the
  API, privacy boundary, scope, and evidence.

### Validation

- Red-first Python 3 tests — five failures because `FitbitResponseError` did not
  exist.
- Focused Python 2.7 and Python 3 mocked suites — 37 tests passed in each
  runtime after implementation.
- Red-first checker-integrity test — proved the checker initially accepted an
  exception that no longer inherited `IOError`.
- Complete local, container, external-directory, and mutation evidence is
  recorded in the completed plan; hosted exact-head verification remains the
  next action.

### Bugs / findings

- P2: callers had to parse human `IOError` strings to distinguish HTTP status,
  size-boundary, and JSON failures.

### Blockers

- Host Python 2 is unavailable; the digest-pinned Python 2.7.18 container and
  hosted workflow remain authoritative for legacy execution.

### Next action

- Run the full exact-head gate, review the PR, and merge only after hosted
  Python 2.7 verification passes.

## 2026-06-26 01:10 PDT - P2 - Define the legacy runtime and current API boundary

### Summary

Documented the exact Python 2 OAuth dependency and made clear that current
Fitbit Web API documentation describes OAuth 2.0 rather than this historical
OAuth 1.0a flow.

### Work completed

- Identified PyPI `oauth==1.0.1` as the package providing
  `from oauth import oauth` and verified its import in the pinned Python 2.7
  container.
- Added disposable-runtime install and import commands without introducing a
  requirements file or dependency installation into CI.
- Added official Fitbit OAuth 2.0 references and a warning against new
  applications, live credentials, or health data.
- Added static README contracts plus a hostile mutation that removes both the
  dependency and current-protocol guidance.
- Updated the roadmap, security posture, README, and completed plan.

### Threads

- Started: none — work completed directly in this maintenance cycle.
- Continued: none.
- Stopped: none.

### Files changed

- `README.md`, `VISION.md`, and `SECURITY.md` — setup, support, and responsible
  use boundaries.
- `scripts/check_legacy_fitbit.py` and `tests/test_checker_integrity.py` — static
  and hostile-mutation coverage.
- `docs/plans/2026-06-26-legacy-runtime-and-fitbit-api-boundary.md` and
  `CHANGES.md` — scope and cycle evidence.

### Validation

- Red phase: the checker accepted a README with both new contracts removed.
- PyPI `oauth==1.0.1` installed and its `OAuthConsumer` import passed in the
  digest-pinned Python 2.7.18 container.
- The checkout-local and absolute-Makefile `make check` gates passed in the
  digest-pinned, network-disabled Python 2.7.18 container, including Python 2
  and Python 3 mocked OAuth suites, both checker-integrity mutations, and 49
  Make target/authority cases.
- `python3 scripts/check_legacy_fitbit.py` and `git diff --check` passed on the
  host; host Python 2 is intentionally unavailable, so the pinned container is
  authoritative for legacy execution.
- `codex review --base origin/master` was attempted but the external service
  returned HTTP 401 before analysis; manual review of the sourced claims,
  install command, static contracts, hostile mutation, and unchanged runtime
  found no actionable issue, and the run continued under the instruction to
  skip auth failures.

### Bugs / findings

- P2: setup named Python 2.7 but omitted the package that satisfies the source
  import.
- P2: the README did not distinguish the historical OAuth 1.0a example from
  Fitbit's currently documented OAuth 2.0 API.

### Blockers

- External Codex review authentication is unavailable in this environment.

### Next action

- Open the focused PR, attempt Codex review, and merge only the exact head after
  hosted checks pass.

## 2026-06-21

- Hardened all six pre-existing Make gates against `MAKEFILE_LIST` and
  `REPO_ROOT` redirection without changing OAuth or token-cache behavior.

## 2026-06-19

- Integrated the tracked environment-only settings loader with the maintained
  OAuth stack and made the dependency-free runtime tests executable under both
  Python 2.7 and current Python 3 versions.
- Rejected malformed and recursively encoded protected-resource paths and
  credential query names, safely encoded authorization tokens, validated OAuth
  token/verifier structure, and added bounded JSON validation.
- Hardened token-cache directory ownership, descriptor identity, size limits,
  destination rechecks, and durable atomic publication.
- Preserved primary network and response failures when cleanup also fails.

## 2026-06-17

- Rejected recursively encoded protected-resource dot segments and encoded
  traversal separators before network creation while preserving valid encoded
  request paths unchanged.

## 2026-06-16

- Published refreshed OAuth token caches through a same-directory staged write
  and atomic rename so handled write failures preserve the last valid token and
  hard-linked targets remain unchanged.

## 2026-06-13

- Rejected symbolic-link token caches for reads and writes and moved owner-only
  read permission checks onto the opened file descriptor.
- Included dangling token-cache symlinks in cache existence checks so existing
  read guards reject them before network access.
- Rejected non-regular token-cache paths before open and required the opened
  descriptor to remain a regular file.
- Ensured OAuth and protected-resource response objects are closed after every
  bounded read attempt, including status, size, and read failures.
- Ensured created HTTPS connections are closed exactly once after cached-token
  and interactive OAuth calls, including HTTP failure paths.

## 2026-06-12

- Added 1 MiB bounded response reads for OAuth token exchanges and protected
  resources, with exact Python 2 read-limit and oversized-payload regressions.
- Stopped printing OAuth token credentials and limited optional debug output to
  non-secret request and response metadata.

## 2026-06-10

- Added digest-pinned Python 2.7 hosted validation that runs the full mocked
  Fitbit OAuth baseline without skipping legacy tests.
- Added credential-free checkout, read-only permissions, CODEOWNERS, and
  sole-workflow enforcement.
- Extended the legacy safety checker to require the CI workflow and completed
  CI plans.
- Added a cached access-token read guard that rejects `access_token.string`
  files with group or other permissions before opening a Fitbit request.
- Added HTTP status validation for OAuth token exchanges and protected resource
  calls without exposing failed response bodies in errors.
## 2026-06-09

- Added bytecode-free verification coverage for the legacy Python 2 tests.
- Switched OAuth request, access-token, and authorization endpoint constants to
  HTTPS and added regression coverage for them.
- Added protected resource API path dot-segment validation, including
  percent-encoded dot segments, before Fitbit network connections open.
- Added a static `make build` gate for the legacy mocked verification flow.
- Added protected resource API path validation so absolute URLs and
  scheme-relative URLs are rejected before any Fitbit network connection opens.
- Added protected resource API path whitespace validation before Fitbit network
  connections open.
- Added protected resource API path fragment validation before Fitbit network
  connections open.
- Added protected resource API path credential-query validation so OAuth tokens
  and client secrets are rejected before Fitbit network connections open.

## 2026-06-08

- Added mocked coverage for the no-cache OAuth request-token/access-token flow
  and owner-only token cache write.
- Added owner-only file permission handling and mocked coverage for the local
  OAuth access-token cache.
- Added `make verify` and `make check` for Python 2 syntax checking and repository-local credential safety checks.
- Disabled debug logging by default so protected URLs and responses are not printed unless explicitly requested.
- Added `access_token.string` to `.gitignore` so the local OAuth token cache stays out of git.
- Added a Python 2 mock-based OAuth request test for the cached-token protected resource path.
- Added canonical `docs/plans` coverage and made `make verify` require the
  completed baseline plan.
