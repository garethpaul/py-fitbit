#!/usr/bin/env bash
set -euo pipefail

grep -q "REQUEST_TOKEN_URL = 'https://%s/oauth/request_token' % SERVER" fitbit.py
grep -q "ACCESS_TOKEN_URL = 'https://%s/oauth/access_token' % SERVER" fitbit.py
grep -q "AUTHORIZATION_URL = 'https://%s/oauth/authorize' % SERVER" fitbit.py

if grep -n "http://%s/oauth/" fitbit.py; then
  echo "Fitbit OAuth endpoints must not use cleartext HTTP" >&2
  exit 1
fi
