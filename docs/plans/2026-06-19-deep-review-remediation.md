# Py-Fitbit Deep Review Remediation

Status: Completed

## Scope

Reconcile the tracked settings root with the maintained Python 2 OAuth stack,
then review URL construction, OAuth parsing, response cleanup, JSON boundaries,
and token-cache publication using hostile dependency-free fixtures.

## Invariants

- Fitbit hosts and OAuth endpoints remain fixed HTTPS constants.
- Protected-resource paths fail closed before signing or network creation when
  percent encoding, traversal, authority syntax, or credential query names are
  ambiguous at any supported decoding layer.
- OAuth tokens and verifiers are bounded, structurally complete, and never
  included in exceptions or debug output.
- Primary request/read/parse failures survive secondary cleanup failures.
- Token caches are bounded owner-only regular files in non-shared writable
  owner-controlled directories, with path/descriptor identity checks and
  durable same-directory atomic publication.
- No live Fitbit credentials or requests are required by verification.

## Verification

The canonical command is `make check`. Local review additionally runs the
Python 3.11, 3.12, 3.13, and 3.14 suites, external-directory Make execution,
hostile source mutations, repository hygiene checks, and hosted Python 2.7
verification on the exact pull-request head.

No live Fitbit OAuth exchange or credentialed protected-resource request was
performed. Current provider compatibility remains unverified.
