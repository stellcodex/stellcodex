#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
SAMPLE_FILE="${SAMPLE_FILE:-}"

echo "== Contract Matrix =="
echo "[1] Smoke"
bash scripts/smoke_test.sh

echo "[2] Runtime forbidden token scan (openapi)"
FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'
if curl -fsS "$BASE_URL/openapi.json" | grep -Eqi "$FORBIDDEN_REGEX"; then
  echo "FAIL: forbidden token appears in openapi.json"
  exit 1
fi
echo "PASS: openapi scan"

echo "[3] Release gate (optional upload chain)"
if [ -n "$SAMPLE_FILE" ]; then
  bash scripts/release_gate.sh
else
  echo "SKIP: provide SAMPLE_FILE to run upload/decision validation"
fi

echo "PASS: contract matrix"
