# Require Regular Token Cache Files

Status: Completed

## Context

The token-cache guards reject symbolic links and verify owner-only permissions
after opening a descriptor. An existing owner-only FIFO can still block forever
inside `os.open` before those descriptor checks run, delaying failure until an
external process timeout and preventing the client from reaching its ordinary
OAuth error boundary.

## Objectives

- Reject existing non-regular token-cache paths before OAuth request
  construction or HTTPS connection creation.
- Keep descriptor-level regular-file validation after open so a path swap
  between preflight and open cannot turn a safe cache into another file type.
- Open token-cache descriptors in nonblocking mode where available so a FIFO
  introduced during that race cannot hang before descriptor validation.
- Preserve regular owner-only cache reads and writes, dangling and existing
  symlink rejection, and the Python 2.7 compatibility contract.
- Add mutation-sensitive static and executable coverage for read and write
  special-file rejection, no-network ordering, and completed evidence.

## Scope Boundaries

- Do not change OAuth endpoints, credential serialization, API paths,
  dependencies, workflows, or public function signatures.
- Do not add live Fitbit requests, credentials, or tracked bytecode.
- Do not attempt to prevent regular-file hard links in this change.

## Implementation Units

### U1. Enforce the regular-file boundary

- Extend token-cache path preflight to reject existing non-regular paths.
- Require the opened descriptor to reference a regular file before reading or
  writing token material.
- Add `O_NONBLOCK` when available to keep race-created FIFOs bounded until the
  descriptor check rejects them.

### U2. Add executable regression coverage

- Exercise owner-only FIFOs at the default cache path for both read and write
  entry points.
- Require deterministic `ValueError` output and prove OAuth request and HTTPS
  constructors are never entered.
- Preserve regular cache, permission, and symlink scenarios.

### U3. Protect the contract and evidence

- Register this plan in the Python 3 static checker.
- Require the preflight, descriptor validation, nonblocking flag, executable
  tests, no-network assertions, and completed verification record.
- Reject isolated mutations that remove or bypass each protection.

## Verification Results

- All 20 focused Python 2.7 tests passed, including direct read and write FIFO
  rejection plus the no-OAuth and no-HTTPS ordering scenario.
- The Python 3 static checker passed with function-scoped contracts for path
  preflight, nonblocking open, descriptor validation, executable tests,
  documentation, and this completed plan.
- Root and external-directory `make check` passed on Python 2.7.18.
- The complete gate passed in the network-disabled, read-only, digest-pinned
  `python:2.7.18` container used by hosted validation.
- Twelve isolated hostile mutations were rejected across nonblocking open,
  path and descriptor checks, read and write wiring, executable FIFO scenarios,
  no-network proof, public documentation, and completed plan evidence.
- Final diff, generated-artifact, credential-pattern, conflict-marker,
  dependency, workflow, and tracked-source audits passed without unrelated
  changes.

## Risks

- `O_NONBLOCK` availability varies by platform, so the source must feature-test
  the flag and preserve ordinary regular-file behavior without it.
- Path preflight alone is racy; descriptor validation remains required even
  after rejecting the initial path type.
