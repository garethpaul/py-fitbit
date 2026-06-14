#!/usr/bin/env python3
"""Repository-local safety checks for the legacy Fitbit OAuth sample."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fitbit.py").read_text()
TEST_SOURCE = (ROOT / "tests" / "test_fitbit_oauth_request.py").read_text()
README = (ROOT / "README.md").read_text()
MAKEFILE = (ROOT / "Makefile").read_text()
CI_PLANS = [
    ROOT / "docs" / "plans" / "2026-06-10-ci-baseline.md",
    ROOT / "docs" / "plans" / "2026-06-10-hosted-legacy-validation.md",
    ROOT / "docs" / "plans" / "2026-06-12-response-body-size-boundary.md",
    ROOT / "docs" / "plans" / "2026-06-12-credential-safe-output.md",
    ROOT / "docs" / "plans" / "2026-06-13-response-close-contract.md",
    ROOT / "docs" / "plans" / "2026-06-13-token-cache-symlink-guard.md",
    ROOT / "docs" / "plans" / "2026-06-13-https-connection-close.md",
    ROOT / "docs" / "plans" / "2026-06-14-location-independent-make.md",
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

connection_close_plan = (
    ROOT / "docs" / "plans" / "2026-06-13-https-connection-close.md"
).read_text()
for evidence in [
    "Canonical `make check` passed",
    "digest-pinned Python 2.7.18 container",
    "Eight hostile mutations",
    "Workflow YAML parsing",
    "secret scanning",
    "generated-artifact scanning",
    "`git diff --check` passed",
]:
    if evidence not in connection_close_plan:
        errors.append(
            "HTTPS connection close plan must preserve verification evidence %s"
            % evidence
        )

location_independent_make_plan = (
    ROOT / "docs" / "plans" / "2026-06-14-location-independent-make.md"
).read_text()
for evidence in [
    "unrelated directory",
    "digest-pinned Python 2.7.18 container",
    "hostile mutations rejected",
    "`git diff --check`",
]:
    if evidence not in location_independent_make_plan:
        errors.append(
            "Location-independent Make plan must preserve verification evidence %s"
            % evidence
        )

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

for make_contract in [
    "override REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))",
    '\t@cd "$(REPO_ROOT)" && for plan in docs/plans/*.md; do \\\n',
    '\tcd "$(REPO_ROOT)" && python2 -c "import py_compile;',
    '\tcd "$(REPO_ROOT)" && python3 scripts/check_legacy_fitbit.py\n',
    '\tcd "$(REPO_ROOT)" && PYTHONDONTWRITEBYTECODE=1 python2 tests/test_fitbit_oauth_request.py\n',
]:
    if make_contract not in MAKEFILE:
        errors.append("Makefile must preserve rooted recipe %s" % make_contract.strip())

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

for forbidden_output in [
    "print 'Auth key:",
    "print 'Auth secret:",
    "print 'Access key:",
    "print 'Access secret:",
    "print 'requested URL:",
    "print 'server response:",
    "set_debuglevel(",
]:
    if forbidden_output in SOURCE:
        errors.append("fitbit.py must not print OAuth credentials or raw exchanges: %s" % forbidden_output)

for safe_debug_output in [
    "OAuth request method: %s",
    "OAuth response status: %s",
    "OAuth response bytes: %s",
]:
    if safe_debug_output not in SOURCE:
        errors.append("fitbit.py must preserve credential-safe debug metadata: %s" % safe_debug_output)

if SOURCE.count("fetch_response(oauth_request, connection, debug=DEBUG)") != 3:
    errors.append("both OAuth exchanges must explicitly use credential-safe debug output")

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

for token_cache_contract in [
    "os.O_NOFOLLOW",
    "os.lstat(fname)",
    "stat.S_ISLNK",
    "os.fstat(fd)",
    "access token cache must not be a symbolic link",
]:
    if token_cache_contract not in SOURCE:
        errors.append("fitbit.py must preserve token-cache symlink guard %s" % token_cache_contract)

for token_cache_test_contract in [
    "test_access_token_cache_rejects_symbolic_links",
    "os.symlink(target, fitbit.ACCESS_TOKEN_STRING_FNAME)",
    "self.assertEqual('target-must-remain-unchanged', token_file.read())",
    "fitbit.write_access_token_string('replacement-secret')",
]:
    if token_cache_test_contract not in TEST_SOURCE:
        errors.append("legacy tests must preserve token-cache symlink regression %s" % token_cache_test_contract)

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

if (
    "MAX_RESPONSE_BODY_BYTES = 1 << 20" not in SOURCE
    or "response.read(MAX_RESPONSE_BODY_BYTES + 1)" not in SOURCE
    or "response exceeds %s bytes" not in SOURCE
):
    errors.append("fitbit.py must bound OAuth and protected response body reads")

response_reader = re.search(
    r"^def read_success_response\(.*?(?=^def |\Z)",
    SOURCE,
    flags=re.MULTILINE | re.DOTALL,
)
if not response_reader or not re.search(
    r"finally:\s+response\.close\(\)", response_reader.group(0)
):
    errors.append("fitbit.py must close every attempted Fitbit response")

fitbit_function = re.search(
    r"^def fitbit\(.*?(?=^if __name__|\Z)",
    SOURCE,
    flags=re.MULTILINE | re.DOTALL,
)
if not fitbit_function or not re.search(
    r"connection = None.*?try:.*?finally:\s+if connection is not None:\s+connection\.close\(\)",
    fitbit_function.group(0),
    flags=re.DOTALL,
):
    errors.append("fitbit.py must close each created HTTPS connection when the call exits")

for connection_test_contract in [
    "self.close_calls = 0",
    "def close(self):",
    "self.close_calls += 1",
    "self.assertEqual(1, connection.close_calls)",
    "self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)",
]:
    if connection_test_contract not in TEST_SOURCE:
        errors.append(
            "legacy tests must preserve HTTPS connection cleanup contract %s"
            % connection_test_contract
        )
if TEST_SOURCE.count("self.assertEqual(1, connection.close_calls)") < 2:
    errors.append("legacy tests must cover cached and interactive success connection cleanup")
if TEST_SOURCE.count("self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)") < 2:
    errors.append("legacy tests must cover OAuth and protected-resource failure connection cleanup")

for test_contract in [
    "test_rejects_oversized_oauth_token_responses",
    "test_rejects_oversized_protected_resource_responses",
    "test_accepts_response_at_size_limit",
    "FakeHTTPResponse.read_sizes",
    "fitbit.MAX_RESPONSE_BODY_BYTES + 1",
    "test_closes_response_when_read_fails",
    "FakeHTTPResponse.instances",
    "response.close_calls",
]:
    if test_contract not in TEST_SOURCE:
        errors.append("legacy tests must preserve %s" % test_contract)

for output_test_contract in [
    "test_debug_output_omits_signed_url_and_response_body",
    "test_debug_mode_does_not_enable_transport_trace_or_log_secrets",
    "request-secret-must-not-be-logged",
    "access-secret-must-not-be-logged",
    "signed-url-secret-must-not-be-logged",
    "response-secret-must-not-be-logged",
    "self.assertEqual([], FakeHTTPSConnection.instances[0].debug_levels)",
    "console_output.count('OAuth request method: GET')",
    "console_output.count('OAuth response status: 200')",
    "self.assertNotIn(oauth_request.http_url, console_output)",
    "self.assertNotIn(response, console_output)",
]:
    if output_test_contract not in TEST_SOURCE:
        errors.append("legacy tests must preserve credential-safe output contract %s" % output_test_contract)

for document_name in ["README.md", "SECURITY.md", "VISION.md", "CHANGES.md"]:
    document = (ROOT / document_name).read_text()
    if "bounded response reads" not in document:
        errors.append("%s must document bounded response reads" % document_name)
    if "response objects are closed" not in document:
        errors.append("%s must document response object cleanup" % document_name)
    if "HTTPS connections are closed" not in document:
        errors.append("%s must document HTTPS connection cleanup" % document_name)

for document_name in ["README.md", "SECURITY.md", "CHANGES.md"]:
    document = (ROOT / document_name).read_text().lower()
    if not re.search(r"debug\s+output", document) or "token" not in document:
        errors.append("%s must document credential-safe OAuth output" % document_name)

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Legacy Fitbit safety checks passed.")
