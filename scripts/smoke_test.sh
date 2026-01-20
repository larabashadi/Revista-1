#!/usr/bin/env bash
set -euo pipefail

BASE=${BASE:-http://localhost:8000}
EMAIL=${EMAIL:-demo@example.com}
PASS=${PASS:-DemoPass123!}

echo "== Register (ignored if exists) =="
curl -s -X POST "$BASE/api/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" >/dev/null || true

echo "== Login =="
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

echo "Token OK"

echo "== Clubs =="
curl -s "$BASE/api/clubs" -H "Authorization: Bearer $TOKEN" | head -c 200 && echo

echo "== Templates =="
curl -s "$BASE/api/templates" -H "Authorization: Bearer $TOKEN" | head -c 200 && echo

echo "Smoke test OK"
