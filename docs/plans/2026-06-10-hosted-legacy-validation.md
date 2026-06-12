# Hosted Legacy Validation

Status: Completed

## Context

The repository requires Python 2.7 for source compilation and mocked OAuth
tests plus Python 3 for repository safety checks. Maintained hosted Python tool
inventories no longer provide Python 2.7, and silently skipping those checks
would make a green workflow misleading.

## Work Completed

- Added GitHub Actions validation in the official Python 2.7.18 image, pinned
  to the reviewed Linux amd64 digest.
- Kept the complete `make check` path, including Python 2 compilation, all
  ten mocked OAuth tests, Python 3 safety checks, bytecode guards, and plan
  validation.
- Limited the workflow token to read-only contents access and pinned checkout
  to a reviewed commit.
- Extended the safety checker to reject floating images, setup-python
  substitutions, skipped legacy tests, allowed failures, or weakened workflow
  contracts.

## Verification

- `make check`
- `docker run --rm --platform linux/amd64 -v "$PWD:/repo" -w /repo python:2.7.18@sha256:c934af72b8bd03b9804d5bde2569c320926e70392d708d113a2e71bcf98c8a20 make check`
- `git diff --check`
