# Legacy Runtime And Fitbit API Boundary Implementation Plan

## Status: Completed

## Goal

Document the exact dependency needed to import the historical sample and make
the current Fitbit OAuth support boundary explicit without changing runtime or
network behavior.

## Architecture

- Keep `fitbit.py` and the pinned Python 2.7 verification image unchanged.
- Treat PyPI `oauth==1.0.1` as an opt-in historical runtime dependency for a
  disposable Python 2 environment, not as a repository development dependency.
- Use current official Fitbit Web API documentation as the source of truth for
  the OAuth 2.0 support statement.
- Enforce the setup and protocol guidance through the existing static checker
  plus a hostile README mutation.

## Scope Boundaries

- Do not add a requirements file, install dependencies in CI, contact Fitbit
  from tests, migrate OAuth protocols, or claim that live OAuth 1.0a requests
  work.
- Do not recommend this sample for new applications or live health data.
- Preserve dependency-free mocked verification under Python 2.7 and Python 3.

## Implementation Tasks

1. Add a checker-integrity mutation that removes the exact dependency and
   current Fitbit OAuth guidance, and verify the unmodified checker misses it.
2. Add static README contracts for the PyPI package, disposable Python 2 setup,
   and current documented OAuth 2.0 boundary.
3. Expand README prerequisites and setup with tested install/import commands,
   official source links, and the no-live-data warning.
4. Move the two completed roadmap items into the maintained baseline and update
   `CHANGES.md`.
5. Run focused checker tests, `make check`, the absolute Makefile gate, the
   digest-pinned Python 2.7 container gate, and `git diff --check`.

## Verification Target

- `python3 tests/test_checker_integrity.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `docker run --rm -v "$PWD:/workspace:ro" -w /workspace python:2.7.18@sha256:c934af72b8bd03b9804d5bde2569c320926e70392d708d113a2e71bcf98c8a20 make check`

## Verification Completed

- Red phase: the existing checker accepted a README with the exact dependency
  and current Fitbit OAuth boundary removed.
- The completed checker-integrity suite rejects that hostile mutation and the
  combined settings-loader bypass mutation.
- PyPI `oauth==1.0.1` installed and exposed `OAuthConsumer` in the
  digest-pinned Python 2.7.18 image.
- Checkout-local and absolute-Makefile gates passed in the digest-pinned,
  network-disabled Python 2.7.18 container, including dual-runtime mocked OAuth
  suites, both checker-integrity mutations, and 49 Make target/authority cases.
- Host static checks and `git diff --check` passed. Hosted verification remains
  required before merge.
