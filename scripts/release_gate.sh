#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
SAMPLE_FILE="${SAMPLE_FILE:-}"

fail(){ echo "FAIL: $1" >&2; exit 1; }
pass(){ echo "PASS: $1"; }

echo "== V7 RELEASE GATE =="

# 1) Health
curl -fsS "$BASE_URL/health" >/dev/null || fail "health endpoint"
pass "health"

# 2) Leak test (runtime, quick grep on key phrases)
# Pull a small known public endpoint response and ensure forbidden tokens absent.
# Adjust endpoint as needed for your app.
FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'
if curl -fsS "$BASE_URL/openapi.json" | grep -Eqi "$FORBIDDEN_REGEX"; then
  fail "forbidden token appears in openapi.json (check naming/leaks)"
fi
pass "openapi forbidden token scan"

# 3) Optional: upload flow if SAMPLE_FILE provided
if [ -n "$SAMPLE_FILE" ]; then
  [ -f "$SAMPLE_FILE" ] || fail "SAMPLE_FILE not found"

  # guest auth (optional)
  if [ -z "$AUTH_TOKEN" ]; then
    AUTH_TOKEN="$(curl -fsS -X POST "$BASE_URL/api/v1/auth/guest" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')"
  fi
  [ -n "$AUTH_TOKEN" ] || fail "guest auth token missing"

  FILE_ID="$(curl -fsS -X POST "$BASE_URL/api/v1/files/upload" -H "Authorization: Bearer $AUTH_TOKEN" -F "upload=@$SAMPLE_FILE" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("file_id",""))')"
  [ -n "$FILE_ID" ] || fail "upload did not return file_id"
  pass "upload returned file_id"

  # status should exist
  curl -fsS -H "Authorization: Bearer $AUTH_TOKEN" "$BASE_URL/api/v1/files/$FILE_ID/status" >/dev/null || fail "status endpoint"
  pass "status endpoint"

  # decision_json endpoint should be reachable (schema validated separately)
  curl -fsS -H "Authorization: Bearer $AUTH_TOKEN" "$BASE_URL/api/v1/orchestrator/decision?file_id=$FILE_ID" >/tmp/decision.json || fail "decision endpoint"
  pass "decision endpoint"

  # validate decision_json (requires python + jsonschema)
  python3 "$(dirname "$0")/validate_decision_json.py" "$(dirname "$0")/../schemas/decision_json.schema.json" /tmp/decision.json || fail "decision_json schema"
  pass "decision_json schema"
else
  echo "NOTE: SAMPLE_FILE not provided; upload/decision checks skipped."
fi

echo "== RELEASE GATE PASS =="
