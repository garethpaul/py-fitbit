# Structured Fitbit Response Errors Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Give callers stable, privacy-safe fields for Fitbit response failures while preserving existing `IOError` compatibility and messages.

**Architecture:** Add one `FitbitResponseError` subclass of `IOError` with `operation`, `reason`, `status`, and `limit` attributes. Raise it for non-2xx responses, oversized bodies, and invalid JSON without parsing or retaining provider error bodies; leave transport exceptions and the successful return type unchanged.

**Tech Stack:** Python 2.7/3, stdlib `unittest`, mocked HTTPS/OAuth fixtures, GNU Make

---

## Status: Completed

### Task 1: Specify The Structured Error Contract

**Files:**
- Modify: `tests/test_fitbit_oauth_request.py`
- Test: `tests/test_fitbit_oauth_request.py`

**Step 1: Write failing assertions**

Extend the existing failed OAuth, failed protected-resource, oversized OAuth,
oversized protected-resource, and malformed JSON tests. Require
`FitbitResponseError`, stable `operation` and `reason` fields, appropriate
`status` or `limit` metadata, and no upstream body content in the exception.

**Step 2: Verify red**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_fitbit_oauth_request.py`

Expected: FAIL because `FitbitResponseError` does not exist.

### Task 2: Implement The Minimal Exception Type

**Files:**
- Modify: `fitbit.py`
- Test: `tests/test_fitbit_oauth_request.py`

**Step 1: Add the exception**

Create a Python 2-compatible `FitbitResponseError(IOError)` that stores the
operation, machine-readable reason, optional status, and optional size limit.
Generate the existing privacy-safe human messages inside the constructor.

**Step 2: Raise it at maintained response boundaries**

Use reason `http_status` for missing/non-2xx status, `response_too_large` for
the one-mebibyte bound, and `invalid_json` for malformed JSON resources.

**Step 3: Verify green**

Run the focused test under Python 3 and the repository's pinned Python 2.7
container. Expected: all tests pass with unchanged response cleanup behavior.

### Task 3: Bind Source, Docs, And Roadmap

**Files:**
- Modify: `scripts/check_legacy_fitbit.py`
- Modify: `tests/test_checker_integrity.py`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-structured-fitbit-response-errors.md`

**Step 1: Add fail-closed source contracts**

Require the exception inheritance, fields, reason values, raise sites, test
assertions, privacy guidance, completed roadmap state, and completed plan.

**Step 2: Add hostile checker mutation**

Remove the structured exception definition in an isolated checker-integrity
fixture and require the checker to fail.

**Step 3: Update maintained guidance**

Document compatibility, stable fields, privacy boundary, and unchanged
transport behavior. Retire the completed structured-error roadmap item without
adding speculative replacement work.

### Task 4: Validate And Ship

**Files:**
- Verify: all changed files

**Step 1: Run complete local gates**

Run: `/usr/bin/make check`

Run from `/tmp`: `/usr/bin/make -f /absolute/path/to/Makefile check`

Run: `git diff --check`

Expected: Python 2/3 tests, checker integrity, docs, Make authority, and static
contracts pass with no repository bytecode.

**Step 2: Review and merge exact head**

Push a focused PR, invoke `$codex-review`, manually verify every finding, wait
for hosted checks, and merge only the exact reviewed green head. Skip
authentication-only skill failures as directed.

## Verification Completed

- The five affected Python 3 tests failed first because
  `FitbitResponseError` did not exist.
- The checker-integrity mutation failed first because the checker accepted a
  structured exception that no longer inherited `IOError`.
- The focused mocked suite passed 37 tests under Python 3 and the
  digest-pinned, network-disabled Python 2.7.18 container.
- `python3 scripts/check_legacy_fitbit.py` and
  `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_checker_integrity.py` passed.
- Checkout-local and external-directory `/usr/bin/make check` passed in the
  digest-pinned Python 2.7.18 container, including both runtime suites, docs,
  root authority, and hostile mutation coverage.
- `git diff --check`, secret scans, and repository-bytecode checks passed.

## Scope Boundaries

- Successful calls still return the same raw response body.
- `FitbitResponseError` remains catchable as `IOError`; transport, file, token,
  input, and OAuth parsing exceptions retain their existing types.
- The exception stores no provider body, URL, token, credential, or health data.
- No endpoint, OAuth signature, cache format, timeout, dependency, workflow, or
  live Fitbit behavior changed.
