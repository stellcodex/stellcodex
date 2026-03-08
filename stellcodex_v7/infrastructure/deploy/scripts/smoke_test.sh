#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

OUT_FILE="${EVIDENCE_DIR}/smoke/smoke_test.txt"
mkdir -p "$(dirname "${OUT_FILE}")"

{
  echo "[smoke-test] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "api_base=${API_BASE}"
  curl -fsS "${API_BASE}/health"
  "${SCRIPT_DIR}/smoke_v7.sh"
  echo "[smoke-test] PASS"
} | tee "${OUT_FILE}"

echo "PASS" > "${EVIDENCE_DIR}/smoke/smoke_test_status.txt"
