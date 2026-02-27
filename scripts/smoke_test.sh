#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
CURL_MAX_TIME="${CURL_MAX_TIME:-5}"

HEALTH_PATHS=(
  /api/v1/admin/health
  /api/v1/health
  /health
  /healthz
  /readyz
  /_health
)

echo "Smoke: health endpoint discovery"
HEALTH_OK_PATH=""
ATTEMPTED_URLS=()
for path in "${HEALTH_PATHS[@]}"; do
  url="${BASE_URL%/}${path}"
  ATTEMPTED_URLS+=("$url")
  if curl -fsS --max-time "$CURL_MAX_TIME" "$url" -o /dev/null 2>/dev/null; then
    HEALTH_OK_PATH="$path"
    break
  fi
done

if [ -z "$HEALTH_OK_PATH" ]; then
  echo "FAIL: no health endpoint returned HTTP 200"
  echo "Tried URLs:"
  for url in "${ATTEMPTED_URLS[@]}"; do
    echo " - $url"
  done
  exit 1
fi

echo "PASS: health endpoint $HEALTH_OK_PATH"
echo "PASS: smoke"
