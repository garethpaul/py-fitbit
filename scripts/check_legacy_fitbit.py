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

if re.search(r"^DEBUG\s*=\s*True\b", SOURCE, flags=re.MULTILINE):
    errors.append("fitbit.py must not enable DEBUG by default")

if "CONSUMER_SECRET" not in SOURCE or "settings.CONSUMER_SECRET" not in SOURCE:
    errors.append("fitbit.py must load the consumer secret from local settings")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Legacy Fitbit safety checks passed.")
