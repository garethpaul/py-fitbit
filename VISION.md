## Py Fitbit Vision

Py Fitbit is a legacy Python OAuth sample for authenticating with the Fitbit
API and fetching protected user resources.

The repository is useful as a compact historical example of OAuth token
exchange, local access-token storage, and direct API calls from Python.

The goal is to preserve the learning value while making the legacy protocol,
Python version, and credential risks explicit.

Current baseline: `make check` verifies Python 2 syntax, repository-local
credential guardrails, mocked OAuth request and token-cache behavior, the static
legacy build gate, and completed `docs/plans` coverage without contacting
Fitbit.

The current focus is:

Priority:

- Preserve the OAuth request, authorize, and access-token flow
- Keep consumer keys and secrets in local settings only
- Treat Python 2 syntax and OAuth 1-era endpoints as legacy
- Maintain `make check` and `make build` for Python 2 syntax and
  credential-safety checks
- Avoid printing or committing real access tokens
- Keep local token-cache files owner-only
- Reject cached access-token files that are readable by group or other users
- Keep cached-token and request-token OAuth branches covered by mocks
- Reject failed OAuth and protected-resource HTTP responses before parsing or
  returning their bodies
- Keep bounded response reads on OAuth and protected-resource payloads
- Keep protected resource calls constrained to Fitbit API paths
- Reject raw whitespace inside protected resource API paths
- Reject URL fragments inside protected resource API paths
- Reject raw and percent-encoded dot segments inside protected resource API
  paths
- Reject credential query parameters inside protected resource API paths
- Keep OAuth endpoints pinned to HTTPS
- Keep legacy verification from leaving Python bytecode in the repository tree
- Run the complete legacy gate in digest-pinned hosted Python 2.7 without
  skipping mocked OAuth coverage
- Keep completed maintenance plans under `docs/plans`
- Keep the static `make check` baseline running in GitHub Actions

Next priorities:

- Expand README setup notes for Python version and dependencies
- Return structured errors instead of printing debug responses by default
- Document whether current Fitbit APIs still support the demonstrated flow

Contribution rules:

- One PR = one focused auth, API, dependency, or documentation change.
- Do not commit credentials, token files, or user health data.
- Add a mock-based test before changing OAuth behavior.
- Keep protocol migrations separate from cleanup.

## Security And Responsible Use

Canonical security policy and reporting:

- [`SECURITY.md`](SECURITY.md)

Fitbit data can include sensitive health and activity information. The sample
should keep credentials local, avoid debug output of tokens or responses, and
make any data access path explicit to the user.

## What We Will Not Merge (For Now)

- Checked-in credentials or access-token files
- Debug logging of protected responses by default
- Silent uploads or forwarding of user data
- OAuth rewrites without compatibility notes

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
