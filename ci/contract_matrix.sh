#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://127.0.0.1:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
SAMPLE_FILE="${SAMPLE_FILE:-}"
RESOLVED_BASE_URL_FILE="${RESOLVED_BASE_URL_FILE:-/tmp/stellcodex_smoke_base_url}"
TARGETS=(docs/contracts schemas)

FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'

RG_EXCLUDES=(
  --glob '!**/.git/**'
  --glob '!**/node_modules/**'
  --glob '!**/*.bak'
  --glob '!**/*.bak.*'
  --glob '!**/*.map'
  --glob '!**/*.png'
  --glob '!**/*.jpg'
  --glob '!**/*.jpeg'
  --glob '!**/*.gif'
  --glob '!**/*.webp'
  --glob '!**/*.svgz'
  --glob '!**/*.pdf'
  --glob '!**/*.zip'
  --glob '!**/*.gz'
  --glob '!**/*.tgz'
  --glob '!**/*.bz2'
  --glob '!**/*.7z'
  --glob '!**/*.woff'
  --glob '!**/*.woff2'
  --glob '!**/*.eot'
  --glob '!**/*.ttf'
  --glob '!**/*.otf'
  --glob '!**/*.mp3'
  --glob '!**/*.mp4'
  --glob '!**/*.mov'
  --glob '!**/*.avi'
  --glob '!**/*.bin'
  --glob '!**/*.exe'
  --glob '!**/*.class'
  --glob '!**/*.jar'
)

echo "== Contract Matrix =="
echo "[1] Smoke"
rm -f "$RESOLVED_BASE_URL_FILE"
BASE_URL="$BASE_URL" \
BACKEND_BASE_URL="$BACKEND_BASE_URL" \
RESOLVED_BASE_URL_FILE="$RESOLVED_BASE_URL_FILE" \
  bash scripts/smoke_test.sh

RUNTIME_BASE_URL="$BASE_URL"
if [ -s "$RESOLVED_BASE_URL_FILE" ]; then
  RUNTIME_BASE_URL="$(head -n 1 "$RESOLVED_BASE_URL_FILE")"
fi

echo "[2] Forbidden token scan (docs/contracts + schemas only)"
SCAN_TARGETS=()
for target in "${TARGETS[@]}"; do
  if [ -d "$target" ]; then
    SCAN_TARGETS+=("$target")
  fi
done

if [ "${#SCAN_TARGETS[@]}" -eq 0 ]; then
  echo "SKIP: no scan targets found (${TARGETS[*]})"
else
  set +e
  scan_output=$(rg --pcre2 -n -i --no-heading -I "${RG_EXCLUDES[@]}" "$FORBIDDEN_REGEX" "${SCAN_TARGETS[@]}")
  rg_status=$?
  set -e

  if [ "$rg_status" -eq 0 ]; then
    echo "FAIL: forbidden token leak detected in public contract/docs/schema files"
    echo "$scan_output"
    exit 1
  fi

  if [ "$rg_status" -ne 1 ]; then
    echo "FAIL: contract leak scan failed to execute (rg exit code $rg_status)"
    exit 1
  fi
fi
echo "PASS: scoped public leak scan"

echo "[3] Runtime openapi reachable"
openapi_code="$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 "$RUNTIME_BASE_URL/openapi.json" || true)"
if [ "$openapi_code" != "200" ]; then
  echo "FAIL: openapi endpoint returned HTTP $openapi_code at $RUNTIME_BASE_URL/openapi.json"
  exit 1
fi
echo "PASS: openapi reachable"

echo "[4] Release gate (optional upload chain)"
if [ -n "$SAMPLE_FILE" ]; then
  BASE_URL="$RUNTIME_BASE_URL" bash scripts/release_gate.sh
else
  echo "SKIP: provide SAMPLE_FILE to run upload/decision validation"
fi

echo "PASS: contract matrix"
