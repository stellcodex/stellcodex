#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-3000}"
SERVER_LOG="${SERVER_LOG:-/tmp/stellcodex_release_gate_server.log}"

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)${PORT}$"; then
  echo "[gate] port ${PORT} already in use -> fallback to 3100"
  PORT=3100
fi
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"

SERVER_PID=""
cleanup() {
  if [ -n "${SERVER_PID}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "[gate] install step (repo standard: npm ci)"
if [ "${FORCE_INSTALL:-0}" = "1" ] || [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
else
  echo "[gate] node_modules present -> skipping npm ci (set FORCE_INSTALL=1 to force)"
fi

echo "[gate] build"
npm run build

echo "[gate] start server on ${BASE_URL}"
STELLCODEX_ENABLE_MOCK_ADMIN=1 npm run start -- -p "${PORT}" >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

READY=0
for _ in $(seq 1 60); do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "[gate] server process exited early"
    tail -n 80 "${SERVER_LOG}" || true
    exit 1
  fi
  code="$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/" || true)"
  if [ "${code}" = "200" ]; then
    READY=1
    break
  fi
  sleep 1
done
if [ "${READY}" -ne 1 ]; then
  echo "[gate] server did not become ready"
  tail -n 80 "${SERVER_LOG}" || true
  exit 1
fi

echo "[gate] route allowlist smoke"
bash scripts/route-allowlist-smoke.sh "${BASE_URL}"

echo "[gate] _next asset smoke"
ASSET_FILE="$(find .next/static -type f -name '*.js' | head -n1 || true)"
if [ -z "${ASSET_FILE}" ]; then
  echo "[gate] FAIL no .next static js asset found"
  exit 1
fi
ASSET_REL="${ASSET_FILE#.next/static/}"
ASSET_URL="${BASE_URL}/_next/static/${ASSET_REL}"
ASSET_CODE="$(curl -sS -o /dev/null -w "%{http_code}" "${ASSET_URL}")"
if [ "${ASSET_CODE}" != "200" ]; then
  echo "[gate] FAIL _next asset ${ASSET_URL} -> ${ASSET_CODE}"
  exit 1
fi
echo "[gate] PASS _next asset (${ASSET_CODE}) ${ASSET_URL}"

echo "[gate] PASS"
