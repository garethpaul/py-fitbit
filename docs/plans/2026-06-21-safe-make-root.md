# Safe Makefile Root Resolution

Status: Completed

## Context

Caller-controlled `MAKEFILE_LIST` redirected Python 2 compilation, Python 3
static checks, credential-safety checks, tests, and documentation validation
outside the reviewed checkout.

## Scope Boundaries

- Do not change OAuth requests, protected-resource validation, token-cache
  behavior, settings loading, or credential output.
- Preserve required Python 2.7 execution and current Python 3 checking.
- Keep all tests mocked and credential-free.

## Work Completed

- Reject command-line and environment replacement of `MAKEFILE_LIST`.
- Canonicalize the checked-in Makefile directory through quoted POSIX tools.
- Add coverage for all six pre-existing public Make targets plus the root regression gate.
- Include the root policy in `make verify` and `make check`.

## Verification Completed

- Python 2.7.18 and Python 3.12.8 passed compilation, all 49 runtime tests,
  the legacy safety checker, and checker integrity regression.
- All 21 target and `REPO_ROOT` override cases passed from a checkout path with
  spaces and an apostrophe.
- Command-line and environment `MAKEFILE_LIST` overrides failed closed.
- Python source, OAuth behavior, settings, and token-cache contracts were unchanged.
