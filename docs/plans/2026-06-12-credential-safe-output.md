# Credential-Safe OAuth Output

Status: Completed

## Context

The interactive request-token flow prints both request-token and access-token
secrets to standard output. The optional debug path also prints signed OAuth
URLs and complete token response bodies. Terminal history, captured build logs,
or redirected output can therefore retain reusable credential material even
though the token cache itself is owner-only.

## Priority

This is a direct credential-disclosure path in normal interactive execution,
not only a hypothetical debug-only concern. The authorization URL still needs
to expose the non-secret request-token key so the user can authorize the
application, but OAuth secrets and raw signed exchanges must never be logged.

## Objectives

- Stop printing request-token and access-token credentials during interactive
  authorization.
- Keep the authorization URL and user-facing progress messages intact.
- Make debug output report only the HTTP method, status, and response size.
- Prove with Python 2 mocks that known secret markers never reach standard
  output while the OAuth flow and token cache continue to work.
- Protect the source, regression tests, documentation, and completed plan with
  the Python 3 static checker.

## Work Completed

- Removed request-token and access-token key and secret prints from the
  interactive authorization flow.
- Disabled the underlying HTTP transport trace and replaced signed URL and raw
  response body debug logging with method, status, and response-size metadata.
- Extended the request-token flow test to prove known request and access token
  secrets stay out of standard output while the authorization URL remains.
- Added focused debug-output regressions using secret-bearing URL and body
  markers, including a full debug-mode flow that forbids transport tracing.
- Extended the Python 3 checker and maintenance documentation to preserve the
  implementation, tests, documentation, and completed plan.

## Verification

- `python2 -c "import py_compile; py_compile.compile('fitbit.py', cfile='/tmp/py-fitbit-fitbit.pyc', doraise=True)"`
- `PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py`
- `python3 scripts/check_legacy_fitbit.py`
- `make check`
- The digest-pinned Python 2.7.18 container passed all 15 mocked tests and the
  complete `make check` gate with networking disabled.
- Seven hostile mutations were rejected: restored access-secret output, raw
  debug response output, and HTTP transport tracing; removed debug-output
  regression, README contract, and explicit safe debug propagation; and an
  incomplete plan status.
- `git diff --check`

## Residual Risk

An additional external-working-directory invocation found that the existing
Makefile resolves `fitbit.py` relative to the caller rather than the Makefile.
The canonical repository-root gate passes; path-independent Make invocation is
separate maintenance work and was not folded into this credential-output fix.
