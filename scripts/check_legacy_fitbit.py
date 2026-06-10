#!/usr/bin/env python3
"""Repository-local safety checks for the legacy Fitbit OAuth sample."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fitbit.py").read_text()
MAKEFILE = (ROOT / "Makefile").read_text()
CI_PLAN = ROOT / "docs" / "plans" / "2026-06-10-hosted-legacy-validation.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
GITIGNORE_LINES = {
    line.strip()
    for line in (ROOT / ".gitignore").read_text().splitlines()
    if line.strip() and not line.strip().startswith("#")
}

errors = []

if not CI_PLAN.exists():
    errors.append("docs/plans/2026-06-10-hosted-legacy-validation.md is missing")
else:
    plan = CI_PLAN.read_text()
    if "Status: Completed" not in plan or "make check" not in plan:
        errors.append("hosted legacy validation plan must be completed and record make check")

if not CI_WORKFLOW.exists():
    errors.append(".github/workflows/check.yml is missing")
else:
    workflow = CI_WORKFLOW.read_text()
    required_fragments = [
        "runs-on: ubuntu-24.04",
        "permissions:\n  contents: read",
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
        "python:2.7.18@sha256:c934af72b8bd03b9804d5bde2569c320926e70392d708d113a2e71bcf98c8a20",
        "run: make check",
    ]
    for fragment in required_fragments:
        if fragment not in workflow:
            errors.append("CI workflow must include %s" % fragment)
    if "setup-python@" in workflow:
        errors.append("CI workflow must use the pinned Python 2 container, not setup-python")
    if "continue-on-error" in workflow:
        errors.append("CI workflow must not allow legacy verification failures")

if "command -v python2" in MAKEFILE or "Skipping legacy Python 2" in MAKEFILE:
    errors.append("Makefile must require Python 2 checks instead of skipping them")

if "access_token.string" not in GITIGNORE_LINES:
    errors.append(".gitignore must ignore access_token.string")

if "__pycache__/" not in GITIGNORE_LINES:
    errors.append(".gitignore must ignore __pycache__/")

bytecode_files = sorted(
    str(path.relative_to(ROOT))
    for path in ROOT.rglob("*.pyc")
    if ".git" not in path.parts
)
bytecode_dirs = sorted(
    str(path.relative_to(ROOT))
    for path in ROOT.rglob("__pycache__")
    if ".git" not in path.parts
)
if bytecode_files or bytecode_dirs:
    generated = bytecode_files + bytecode_dirs
    errors.append(
        "Python bytecode files must not be kept in the repository tree: %s"
        % ", ".join(generated)
    )

if re.search(r"^DEBUG\s*=\s*True\b", SOURCE, flags=re.MULTILINE):
    errors.append("fitbit.py must not enable DEBUG by default")

if "CONSUMER_SECRET" not in SOURCE or "settings.CONSUMER_SECRET" not in SOURCE:
    errors.append("fitbit.py must load the consumer secret from local settings")

if "write_access_token_string" not in SOURCE or "0600" not in SOURCE:
    errors.append("fitbit.py must write access_token.string with owner-only permissions")

if "read_access_token_string" not in SOURCE:
    errors.append("fitbit.py must read access_token.string through a token helper")

if (
    "stat.S_IMODE" not in SOURCE
    or "stat.S_IRWXG" not in SOURCE
    or "stat.S_IRWXO" not in SOURCE
):
    errors.append("fitbit.py must reject access_token.string with group or other permissions")

if "validate_api_call" not in SOURCE:
    errors.append("fitbit.py must validate protected Fitbit API paths")

if "http://%s/oauth" in SOURCE:
    errors.append("fitbit.py must use HTTPS for OAuth endpoints")

if (
    "api_call.startswith('//')" not in SOURCE
    or ("'://' in api_call" not in SOURCE and "\"://\" in api_call" not in SOURCE)
):
    errors.append("fitbit.py must reject absolute and scheme-relative API calls")

if ".isspace()" not in SOURCE:
    errors.append("fitbit.py must reject whitespace inside protected API paths")

if "'#' in api_call" not in SOURCE and '"#" in api_call' not in SOURCE:
    errors.append("fitbit.py must reject fragments inside protected API paths")

if "path_segments" not in SOURCE or "'.', '..'" not in SOURCE or "urlparse.unquote" not in SOURCE:
    errors.append("fitbit.py must reject dot segments inside protected API paths")

if "CREDENTIAL_QUERY_PARAMETERS" not in SOURCE or "urlparse.parse_qsl" not in SOURCE:
    errors.append("fitbit.py must reject credential query parameters inside protected API paths")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Legacy Fitbit safety checks passed.")
