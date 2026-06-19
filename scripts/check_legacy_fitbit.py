#!/usr/bin/env python3
"""Repository-local safety checks for the legacy Fitbit OAuth sample."""

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fitbit.py").read_text()
MAKEFILE = (ROOT / "Makefile").read_text()
README = (ROOT / "README.md").read_text()
SETTINGS_PATH = ROOT / "settings.py"
SETTINGS_TEST_PATH = ROOT / "tests" / "test_settings.py"
STALE_CHECKER_PATH = ROOT / "scripts" / "check-baseline.sh"
CI_PLAN = ROOT / "docs" / "plans" / "2026-06-10-hosted-legacy-validation.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
GITIGNORE_LINES = {
    line.strip()
    for line in (ROOT / ".gitignore").read_text().splitlines()
    if line.strip() and not line.strip().startswith("#")
}

errors = []


def string_literal(node):
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    return None


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

settings_test_command = (
    "\tPYTHONDONTWRITEBYTECODE=1 python2 tests/test_settings.py"
)
if MAKEFILE.splitlines().count(settings_test_command) != 1:
    errors.append("Makefile must run tests/test_settings.py under required Python 2")

if not SETTINGS_TEST_PATH.exists():
    errors.append("tests/test_settings.py is missing")

if STALE_CHECKER_PATH.exists():
    errors.append(
        "scripts/check-baseline.sh must be removed after its checks move into the canonical gate"
    )

if not SETTINGS_PATH.exists():
    errors.append("settings.py is missing")
else:
    settings_source = SETTINGS_PATH.read_text()
    try:
        settings_tree = ast.parse(settings_source)
    except SyntaxError as exc:
        errors.append("settings.py must parse under Python 3: %s" % exc)
    else:
        expected_assignments = {
            "CONSUMER_KEY": "FITBIT_CONSUMER_KEY",
            "CONSUMER_SECRET": "FITBIT_CONSUMER_SECRET",
        }
        found_assignments = {name: [] for name in expected_assignments}
        for node in ast.walk(settings_tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in found_assignments:
                found_assignments[target.id].append(node.value)

        for name, environment_name in expected_assignments.items():
            assignments = found_assignments[name]
            if len(assignments) != 1:
                errors.append("settings.py must assign %s exactly once" % name)
                continue
            value = assignments[0]
            valid_call = (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "_required_env"
                and len(value.args) == 1
                and not value.keywords
                and string_literal(value.args[0]) == environment_name
            )
            if not valid_call:
                errors.append(
                    "settings.py must load %s only from %s"
                    % (name, environment_name)
                )

        environment_get_calls = [
            node
            for node in ast.walk(settings_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "environ"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
        ]
        if len(environment_get_calls) != 1:
            errors.append("settings.py must use one os.environ.get lookup")
        elif (
            len(environment_get_calls[0].args) != 1
            or environment_get_calls[0].keywords
        ):
            errors.append("settings.py must not define an environment fallback value")

    for environment_name in ("FITBIT_CONSUMER_KEY", "FITBIT_CONSUMER_SECRET"):
        if environment_name not in settings_source:
            errors.append("settings.py must reference %s" % environment_name)
        if environment_name not in README:
            errors.append("README.md must document %s" % environment_name)

if "settings.py" in GITIGNORE_LINES:
    errors.append(".gitignore must not ignore the tracked settings.py module")

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

if "read_success_response" not in SOURCE or "status < 200" not in SOURCE or "status >= 300" not in SOURCE:
    errors.append("fitbit.py must reject non-2xx Fitbit HTTP responses")

if "read_success_response(resp, 'protected resource request')" not in SOURCE:
    errors.append("protected Fitbit resource calls must enforce HTTP status checks")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Legacy Fitbit safety checks passed.")
