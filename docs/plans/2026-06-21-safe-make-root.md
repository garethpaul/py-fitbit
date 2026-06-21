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
- Canonicalize the checked-in Makefile directory with pinned POSIX tools and export it only to recipes.
- Add executed coverage for all six pre-existing public Make targets plus the root regression gate.
- Include the root policy in `make verify` and `make check`.

## Verification Completed

- 49 executed target and authority cases kept quality commands inside the checkout.
- Hostile checkout backticks were blocked and dollar-substitution paths failed closed.
- `MAKEFILES`, `SHELL`, and `.SHELLFLAGS` authority were covered. Python command names remain repository-owned.
- Command-line and environment `MAKEFILE_LIST` overrides failed closed.
- `make check` remains the complete repository gate and no runtime source changed.
