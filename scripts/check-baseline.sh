#!/usr/bin/env bash
set -euo pipefail

test -f settings.py
! grep -qx "settings.py" .gitignore
grep -q "FITBIT_CONSUMER_KEY" settings.py README.md
grep -q "FITBIT_CONSUMER_SECRET" settings.py README.md

python3 -B - <<'PY'
from pathlib import Path

compile(Path("settings.py").read_text(), "settings.py", "exec")
PY
FITBIT_CONSUMER_KEY=key FITBIT_CONSUMER_SECRET=secret python3 -B - <<'PY'
import settings

assert settings.CONSUMER_KEY == "key"
assert settings.CONSUMER_SECRET == "secret"
PY

missing_output="$(env -u FITBIT_CONSUMER_KEY -u FITBIT_CONSUMER_SECRET python3 -B -c "import settings" 2>&1 || true)"
if echo "$missing_output" | grep -q "Missing required environment variable FITBIT_CONSUMER_KEY"; then
  :
else
  echo "settings.py must fail clearly when required Fitbit credentials are missing" >&2
  exit 1
fi

if grep -R "CONSUMER_SECRET *= *['\"][^'\"]" -n settings.py; then
  echo "Do not commit real Fitbit consumer secrets" >&2
  exit 1
fi
