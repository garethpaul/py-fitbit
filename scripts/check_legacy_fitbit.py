#!/usr/bin/env python3
"""Repository-local safety checks for the legacy Fitbit OAuth sample."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fitbit.py").read_text()
GITIGNORE_LINES = {
    line.strip()
    for line in (ROOT / ".gitignore").read_text().splitlines()
    if line.strip() and not line.strip().startswith("#")
}

errors = []

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
