#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
echo "Smoke: health"
curl -fsS "$BASE_URL/health" >/dev/null

echo "Smoke: openapi reachable"
curl -fsS "$BASE_URL/openapi.json" >/dev/null

echo "PASS: smoke"
