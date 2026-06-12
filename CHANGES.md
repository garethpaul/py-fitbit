# Changes

## 2026-06-12

- Added 1 MiB bounded response reads for OAuth token exchanges and protected
  resources, with exact Python 2 read-limit and oversized-payload regressions.

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
