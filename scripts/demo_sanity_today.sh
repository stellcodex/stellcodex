#!/usr/bin/env bash
set -euo pipefail

FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

echo "[demo] started_at=$(date -Iseconds)"
echo "[demo] frontend=http://127.0.0.1:${FRONTEND_PORT}/"
echo "[demo] backend_base=http://127.0.0.1:${BACKEND_PORT}"

echo

echo "[demo] frontend HEAD check"
frontend_code="$(curl -sS -o /tmp/demo_frontend_head.txt -w "%{http_code}" -I "http://127.0.0.1:${FRONTEND_PORT}/" || true)"
echo "frontend_http=${frontend_code}"
sed -n "1,20p" /tmp/demo_frontend_head.txt
if [ "${frontend_code}" != "200" ]; then
  echo "[demo] FAIL: frontend head returned HTTP ${frontend_code}" >&2
  exit 1
fi

echo

echo "[demo] backend health check (/api/v1/health)"
backend_code="$(curl -sS -o /tmp/demo_backend_health.json -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" || true)"
echo "backend_health_http=${backend_code}"
sed -n "1,40p" /tmp/demo_backend_health.json
if [ "${backend_code}" != "200" ]; then
  echo "[demo] FAIL: backend health returned HTTP ${backend_code}" >&2
  exit 1
fi

echo

echo "[demo] admin failures probe"
admin_code="$(curl -sS -o /tmp/demo_admin_failures_body.txt -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}/api/v1/admin/failures" || true)"
echo "admin_failures_http=$admin_code"
if [ "$admin_code" = "200" ] || [ "$admin_code" = "401" ] || [ "$admin_code" = "403" ]; then
  sed -n "1,40p" /tmp/demo_admin_failures_body.txt
fi

echo
echo "[demo] RESULT=PASS"
echo "[demo] completed_at=$(date -Iseconds)"
