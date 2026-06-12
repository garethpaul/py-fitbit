# Fitbit Response Body Size Boundary

Status: Completed

## Context

The shared OAuth and protected-resource response helper calls `response.read()`
without a size. A malicious, broken, or misconfigured endpoint can therefore
force this legacy process to allocate an unbounded response before status or
payload handling completes.

## Priority

OAuth responses contain credential material and protected resources may contain
private health data. Both paths need a deterministic memory boundary that does
not copy oversized response content into exceptions.

## Objectives

- Limit every Fitbit HTTP response read to 1 MiB plus one detection byte.
- Reject oversized OAuth and protected-resource responses with stable errors.
- Keep upstream body content out of exception messages.
- Assert the exact bounded read size in Python 2 mocks.
- Protect the implementation, tests, docs, and completed plan in the Python 3
  static checker.

## Verification

- `python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"`
- `PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- `git diff --check`

## Work Completed

- `read_success_response` reads at most 1 MiB plus one detection byte for every
  OAuth and protected-resource response.
- Successful oversized responses fail before token parsing, token-cache writes,
  or protected-data return.
- Stable errors report only the operation and size boundary, never response
  body content.
- Python 2 mocks record the requested read size, and the static checker protects
  the implementation, both regressions, documentation, and this completed plan.

## Verification Results

- Python 2 compilation passed without writing bytecode into the repository.
- All 13 mocked Python 2 OAuth tests passed, including acceptance exactly at
  the 1 MiB boundary.
- `python3 scripts/check_legacy_fitbit.py` passed.
- `make lint`, `make test`, `make build`, `make docs`, `make verify`, and
  `make check` passed locally with Python 2.7.18 and Python 3.12.8.
- Caller-independent Python 3 static checking from `/` passed.
- `make check` passed in the exact digest-pinned Python 2.7.18 container used by
  hosted CI.
- All 11 hostile plan, implementation, oversized-path, exact-boundary,
  read-size-proof, and documentation mutations were rejected.
- `git diff --check` passed, and no `.pyc` or `__pycache__` artifacts were
  created in the repository.
