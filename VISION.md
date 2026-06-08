## Py Fitbit Vision

Py Fitbit is a legacy Python OAuth sample for authenticating with the Fitbit
API and fetching protected user resources.

The repository is useful as a compact historical example of OAuth token
exchange, local access-token storage, and direct API calls from Python.

The goal is to preserve the learning value while making the legacy protocol,
Python version, and credential risks explicit.

The current focus is:

Priority:

- Preserve the OAuth request, authorize, and access-token flow
- Keep consumer keys and secrets in local settings only
- Treat Python 2 syntax and OAuth 1-era endpoints as legacy
- Maintain `make verify` for Python 2 syntax and credential-safety checks
- Avoid printing or committing real access tokens

Next priorities:

- Expand README setup notes for Python version and dependencies
- Move token-file handling behind a safer storage abstraction
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
