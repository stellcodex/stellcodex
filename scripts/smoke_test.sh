#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/runtime_env.sh"

BASE_URL="${BASE_URL:-}"
BACKEND_BASE_URL="${BACKEND_BASE_URL:-}"
CURL_MAX_TIME="${CURL_MAX_TIME:-5}"
RESOLVED_BASE_URL_FILE="${RESOLVED_BASE_URL_FILE:-/tmp/stellcodex_smoke_base_url}"

HEALTH_PATHS=(
  /api/v1/admin/health
  /api/v1/health
  /health
  /healthz
  /readyz
  /_health
)

BASE_URL_CANDIDATES=()

add_base_url_candidate() {
  local candidate="$1"
  local existing=""

  if [ -z "$candidate" ]; then
    return
  fi

  for existing in "${BASE_URL_CANDIDATES[@]:-}"; do
    if [ "$existing" = "$candidate" ]; then
      return
    fi
  done

  BASE_URL_CANDIDATES+=("$candidate")
}

add_base_url_candidate "$BASE_URL"
add_base_url_candidate "$BACKEND_BASE_URL"
add_base_url_candidate "$(runtime_resolve_backend_base_url 2>/dev/null || true)"
add_base_url_candidate "http://127.0.0.1:8000"

echo "Smoke: health endpoint discovery"
HEALTH_OK_PATH=""
HEALTH_OK_BASE_URL=""
ATTEMPTED_URLS=()
for base_url in "${BASE_URL_CANDIDATES[@]}"; do
  for path in "${HEALTH_PATHS[@]}"; do
    url="${base_url%/}${path}"
    ATTEMPTED_URLS+=("$url")
    http_code="$(curl -sS -o /dev/null -w "%{http_code}" --max-time "$CURL_MAX_TIME" "$url" 2>/dev/null || true)"
    if [ "$http_code" = "200" ]; then
      HEALTH_OK_PATH="$path"
      HEALTH_OK_BASE_URL="$base_url"
      break 2
    fi
  done
done

if [ -z "$HEALTH_OK_PATH" ]; then
  echo "FAIL: no health endpoint returned HTTP 200"
  echo "Tried URLs:"
  for url in "${ATTEMPTED_URLS[@]}"; do
    echo " - $url"
  done
  exit 1
fi

printf '%s\n' "$HEALTH_OK_BASE_URL" > "$RESOLVED_BASE_URL_FILE"
echo "PASS: health endpoint $HEALTH_OK_PATH via $HEALTH_OK_BASE_URL"
echo "PASS: smoke"
