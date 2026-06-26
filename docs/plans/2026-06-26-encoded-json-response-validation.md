# Encoded JSON Response Validation Implementation Plan

**Goal:** Validate malformed JSON responses for encoded `.json` protected-resource paths without changing the signed request target.

**Architecture:** Reuse the existing bounded percent-decoding iterator only to classify whether a protected-resource path represents a JSON endpoint. Keep OAuth signing, HTTPS transmission, response size limits, and structured errors unchanged.

**Tech Stack:** Python 2.7/3, stdlib `unittest`, mocked HTTPS/OAuth fixtures, GNU Make

---

## Status: Completed

### Task 1: Reproduce The Validation Gap

- Added a mocked request for `/1/user/-/profile%2Ejson` with a malformed body.
- Verified the test failed because no `FitbitResponseError` was raised.
- Required the signed and transmitted request target to remain byte-for-byte unchanged.

### Task 2: Implement Bounded Classification

- Added a helper that checks each existing bounded decoding layer for a `.json` suffix.
- Used the helper only to select JSON validation after the response is read.
- Kept request validation responsible for malformed or excessive encoding.

### Task 3: Bind The Contract

- Added static source, regression-test, and maintained-documentation requirements.
- Added a hostile mutation that restores raw-path-only classification and requires the checker to reject it.
- JSON response validation follows bounded percent-decoding of the protected-resource path without rewriting the signed request target.

### Task 4: Verify And Ship

- Run `make check` in the digest-pinned, network-disabled Python 2.7.18 container.
- Run focused Python 3 tests, checker integrity, and `git diff --check`.
- Review and merge only the exact hosted-green head.

## Verification Completed

- Red-first Python 3 test reproduced the missing structured error.
- Focused Python 3 mocked OAuth suite passed 38 tests after implementation.
- Digest-pinned, network-disabled Python 2.7.18 `make check` passed the Python 2 and Python 3 OAuth suites with 38 tests each, both settings suites with 12 tests each, all 4 checker-integrity tests, and all 49 Make authority cases.
- `git diff --check` passed.
- Hosted Python 2.7 verification and CodeQL passed on PR #20.
- The Codex review helper returned HTTP 401 before analysis; an immutable manual review confirmed the local and PR heads matched and found no actionable issue.

## Scope Boundaries

- The request path remains unchanged for OAuth signing and HTTPS transmission.
- Successful calls still return the same raw response body.
- No provider response body is stored or exposed.
- No endpoint, cache, dependency, workflow, or live Fitbit behavior changed.
