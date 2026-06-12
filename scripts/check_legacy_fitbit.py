#!/usr/bin/env python3
"""Repository-local safety checks for the legacy Fitbit OAuth sample."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fitbit.py").read_text()
README = (ROOT / "README.md").read_text()
MAKEFILE = (ROOT / "Makefile").read_text()
CI_PLANS = [
    ROOT / "docs" / "plans" / "2026-06-10-ci-baseline.md",
    ROOT / "docs" / "plans" / "2026-06-10-hosted-legacy-validation.md",
]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
GITIGNORE_LINES = {
    line.strip()
    for line in (ROOT / ".gitignore").read_text().splitlines()
    if line.strip() and not line.strip().startswith("#")
}

errors = []

if "access_token.string" not in GITIGNORE_LINES:
    errors.append(".gitignore must ignore access_token.string")

for ci_plan in CI_PLANS:
    if not ci_plan.exists():
        errors.append("%s is missing" % ci_plan.relative_to(ROOT))
        continue
    plan = ci_plan.read_text()
    if "Status: Completed" not in plan or "make check" not in plan:
        errors.append("%s must be completed and record make check" % ci_plan.relative_to(ROOT))

if not CI_WORKFLOW.exists():
    errors.append(".github/workflows/check.yml is missing")
else:
    workflow = CI_WORKFLOW.read_text()
    required_fragments = [
        "runs-on: ubuntu-24.04",
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
        "persist-credentials: false",
        "python:2.7.18@sha256:c934af72b8bd03b9804d5bde2569c320926e70392d708d113a2e71bcf98c8a20",
        "run: make check",
    ]
    for fragment in required_fragments:
        if fragment not in workflow:
            errors.append("CI workflow must include %s" % fragment)
    if workflow.count("actions/checkout@") != 1:
        errors.append("CI workflow must use exactly one checkout action")
    if workflow.count("persist-credentials:") != 1:
        errors.append("CI workflow must set checkout credential persistence exactly once")
    if workflow.count("permissions:") != 1 or re.search(r"^\s+[\w-]+:\s+write\s*$", workflow, re.MULTILINE):
        errors.append("CI workflow must keep one read-only permissions block")
    if "setup-python@" in workflow:
        errors.append("CI workflow must use the pinned Python 2 container, not setup-python")
    if "continue-on-error" in workflow:
        errors.append("CI workflow must not allow legacy verification failures")
    if "branches:" in workflow:
        errors.append("CI workflow must validate pushes on every branch")

workflow_files = sorted(
    str(path.relative_to(ROOT))
    for path in (ROOT / ".github" / "workflows").rglob("*")
    if path.is_file()
)
if workflow_files != [".github/workflows/check.yml"]:
    errors.append("check.yml must be the repository's only hosted workflow")

if not CODEOWNERS.exists() or CODEOWNERS.read_text().strip() != "* @garethpaul":
    errors.append("CODEOWNERS must assign the repository to @garethpaul")

if "GitHub Actions" not in README:
    errors.append("README must document the GitHub Actions check")

if "command -v python2" in MAKEFILE or "Skipping legacy Python 2" in MAKEFILE:
    errors.append("Makefile must require Python 2 checks instead of skipping them")

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

if "read_success_response" not in SOURCE or "status < 200" not in SOURCE or "status >= 300" not in SOURCE:
    errors.append("fitbit.py must reject non-2xx Fitbit HTTP responses")

if "read_success_response(resp, 'protected resource request')" not in SOURCE:
    errors.append("protected Fitbit resource calls must enforce HTTP status checks")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Legacy Fitbit safety checks passed.")
