# py-fitbit

<!-- README-OVERVIEW-IMAGE -->
![Project overview](docs/readme-overview.svg)

## Overview

`garethpaul/py-fitbit` is a public sample, documentation, or utility project. Fitbit Auth

This README is based on the checked-in source, manifests, scripts, and repository metadata on the `master` branch. The project language mix found during review was: Python (1).

## Repository Contents

- `README.md` - project overview and local usage notes
- `.github/workflows/check.yml` - pinned Python 2.7 hosted verification
- `CHANGES.md` - notable maintenance changes
- `Makefile` - local verification entry points
- `settings.py` - tracked, secret-free environment loader
- `docs/plans` - canonical completed maintenance plans
- `plans` - completed maintenance plans
- `scripts` - deterministic legacy safety checks
- `SECURITY.md` - security reporting and disclosure guidance
- `tests` - Python 2 settings-contract and mocked OAuth request tests
- `VISION.md` - project direction and maintenance guardrails

Additional scan context:

- Source directories: scripts, tests
- Dependency and build manifests: Makefile
- Entry points or build surfaces: fitbit.py, Makefile
- Test-looking files: scripts/check_legacy_fitbit.py, tests/test_settings.py, tests/test_fitbit_oauth_request.py

## Getting Started

### Prerequisites

- Git
- Python 2.7 for the legacy sample syntax check
- Python 3 for repository safety checks
- `make`

### Setup

```bash
git clone https://github.com/garethpaul/py-fitbit.git
cd py-fitbit
```

The setup commands above are derived from repository files. Legacy mobile, Python, or JavaScript samples may require older SDKs or package versions than a modern workstation uses by default.

## Running or Using the Project

- Set `FITBIT_CONSUMER_KEY` and `FITBIT_CONSUMER_SECRET` in the environment.
  The tracked `settings.py` loader rejects unset, empty, and whitespace-only
  values plus common placeholder forms before a Fitbit request can be opened.
  This only rejects known placeholders; it does not validate credentials with
  Fitbit. The loader does not read local files.
- Run `fitbit.py` with Python 2.7 if you need to exercise the legacy OAuth 1 flow.
- OAuth request, access-token, and authorization endpoints are pinned to
  `https://api.fitbit.com`.
- Pass protected-resource calls as Fitbit API paths such as
  `/1/user/-/profile.json`; absolute URLs and scheme-relative URLs are rejected
  before a network connection is opened.
- Protected-resource paths are trimmed at the edges but must not contain raw
  whitespace or control characters.
- Protected-resource paths must not include URL fragments.
- Protected-resource paths must not include raw or percent-encoded `.` or `..`
  path segments.
- Protected-resource paths must not include credential query parameters such as
  `oauth_token`, `access_token`, or `client_secret`; OAuth credentials belong
  in the signed request header or local settings.
- `access_token.string` is a local token cache, must stay untracked, and is
  written with owner-only permissions. Existing token-cache files with group or
  other permissions are rejected before a Fitbit network request is opened.
- OAuth token exchanges and protected resource calls reject non-2xx HTTP
  responses without including the upstream response body in the exception.

## Testing and Verification

- Run `make check` before committing changes.
- Run `make build` for the static legacy verification gate; it uses the same
  Python 2 settings-contract and mocked OAuth tests as `make test`.
- `make check` delegates to `make verify`, which compiles the Python 2 source,
  checks that credential/token handling stays local, keeps debug logging
  disabled by default, independently verifies the settings runtime contract,
  runs the settings-contract suite and mocked OAuth
  request, request-token flow, API path validation, and token-cache suite
  without contacting Fitbit, and verifies completed plans under `docs/plans`.
- The test target disables Python bytecode writes, and the legacy safety check
  rejects checked-out `.pyc` files or `__pycache__` directories.
- GitHub Actions runs the complete gate in the official Python 2.7.18 image,
  pinned by digest, with read-only repository permissions. The job does not
  skip Python 2 compilation or either Python 2 test suite.

When the required SDK or runtime is unavailable, use static checks and source review first, then verify on a machine that has the matching platform toolchain.

## Configuration and Secrets

- Keep API keys, OAuth credentials, tokens, and account-specific values out of
  the repository. Supply the required Fitbit consumer key and secret through
  `FITBIT_CONSUMER_KEY` and `FITBIT_CONSUMER_SECRET`.
- `access_token.string` remains generated, untracked, and owner-only.
- The legacy `oauth2` dependency is undeclared, and compatibility with Fitbit's
  current OAuth service has not been verified.

## Security and Privacy Notes

- Review changes touching authentication or token handling; examples from the scan include fitbit.py.
- Review changes touching external API calls or credential-adjacent configuration; examples from the scan include fitbit.py.
- Review changes touching file, media, JSON, XML, CSV, OCR, or data parsing; examples from the scan include fitbit.py.
- Protected Fitbit resource paths reject embedded whitespace before network
  requests are opened.
- Protected Fitbit resource paths reject fragments before network requests are
  opened.
- Protected Fitbit resource paths reject raw and percent-encoded `.` and `..`
  path segments before network requests are opened.
- Protected Fitbit resource paths reject credential query parameters before
  network requests are opened.
- Existing `access_token.string` files must be owner-only; readable-by-group or
  readable-by-other cache files are rejected before network requests are
  opened.

## Maintenance Notes

- See `SECURITY.md` for vulnerability reporting and safe research guidance.
- See `VISION.md` for project direction and contribution guardrails.
- See `docs/plans/2026-06-08-py-fitbit-baseline.md` for the canonical legacy
  safety and mocked OAuth request baseline.
- See `docs/plans/2026-06-08-token-cache-permissions.md` for the token-cache
  permissions baseline.
- See `docs/plans/2026-06-08-request-token-flow-test.md` for the mocked
  no-cache OAuth flow baseline.
- See `docs/plans/2026-06-09-api-call-path-validation.md` for the protected
  resource API path guard.
- See `docs/plans/2026-06-09-api-call-whitespace-validation.md` for the
  protected resource path whitespace guard.
- See `docs/plans/2026-06-09-api-call-fragment-validation.md` for the
  protected resource path fragment guard.
- See `docs/plans/2026-06-09-api-call-dot-segment-validation.md` for the
  protected resource path dot-segment guard and static `make build` alias.
- See `docs/plans/2026-06-09-api-call-credential-query-validation.md` for the
  protected resource path credential-query guard.
- See `docs/plans/2026-06-09-oauth-endpoint-https.md` for the OAuth endpoint
  HTTPS guard.
- See `docs/plans/2026-06-09-bytecode-free-verification.md` for the
  bytecode-free legacy verification guard.
- See `docs/plans/2026-06-10-token-cache-read-permissions.md` for the
  token-cache read permission guard.
- See `docs/plans/2026-06-10-hosted-legacy-validation.md` for digest-pinned,
  full Python 2.7 hosted verification.
- See `docs/plans/2026-06-10-http-status-validation.md` for OAuth and protected
  resource response status validation.
- See `docs/plans/2026-06-19-tracked-settings-module.md` for the tracked,
  fail-closed environment loader and canonical gate integration.

## Contributing

Keep changes small and tied to the project that is already present in this repository. For code changes, document the toolchain used, avoid committing generated dependency directories or local configuration, and update this README when setup or verification steps change.
