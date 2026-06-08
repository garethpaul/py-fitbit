# py-fitbit

<!-- README-OVERVIEW-IMAGE -->
![Project overview](docs/readme-overview.svg)

## Overview

`garethpaul/py-fitbit` is a public sample, documentation, or utility project. Fitbit Auth

This README is based on the checked-in source, manifests, scripts, and repository metadata on the `master` branch. The project language mix found during review was: Python (1).

## Repository Contents

- `README.md` - project overview and local usage notes
- `CHANGES.md` - notable maintenance changes
- `Makefile` - local verification entry points
- `docs/plans` - canonical completed maintenance plans
- `plans` - completed maintenance plans
- `scripts` - deterministic legacy safety checks
- `SECURITY.md` - security reporting and disclosure guidance
- `tests` - Python 2 mock-based tests for the legacy OAuth request path
- `VISION.md` - project direction and maintenance guardrails

Additional scan context:

- Source directories: scripts, tests
- Dependency and build manifests: Makefile
- Entry points or build surfaces: fitbit.py, Makefile
- Test-looking files: scripts/check_legacy_fitbit.py, tests/test_fitbit_oauth_request.py

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

- Create a local, untracked `settings.py` with `CONSUMER_KEY` and `CONSUMER_SECRET`.
- Run `fitbit.py` with Python 2.7 if you need to exercise the legacy OAuth 1 flow.
- `access_token.string` is a local token cache and must stay untracked.

## Testing and Verification

- Run `make check` before committing changes.
- `make check` delegates to `make verify`, which compiles the Python 2 source, checks that credential/token handling stays local, keeps debug logging disabled by default, runs a mocked OAuth request test without contacting Fitbit, and verifies the canonical completed plan under `docs/plans`.

When the required SDK or runtime is unavailable, use static checks and source review first, then verify on a machine that has the matching platform toolchain.

## Configuration and Secrets

- Detected references to Fitbit. Keep API keys, OAuth credentials, tokens, and account-specific values in local configuration only.

## Security and Privacy Notes

- Review changes touching authentication or token handling; examples from the scan include fitbit.py.
- Review changes touching external API calls or credential-adjacent configuration; examples from the scan include fitbit.py.
- Review changes touching file, media, JSON, XML, CSV, OCR, or data parsing; examples from the scan include fitbit.py.

## Maintenance Notes

- See `SECURITY.md` for vulnerability reporting and safe research guidance.
- See `VISION.md` for project direction and contribution guardrails.
- See `docs/plans/2026-06-08-py-fitbit-baseline.md` for the canonical legacy
  safety and mocked OAuth request baseline.

## Contributing

Keep changes small and tied to the project that is already present in this repository. For code changes, document the toolchain used, avoid committing generated dependency directories or local configuration, and update this README when setup or verification steps change.
