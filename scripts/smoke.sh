#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[smoke] frontend build"
(
  cd "${ROOT_DIR}/frontend"
  npm run build
)

echo "[smoke] backend unittest"
(
  cd "${ROOT_DIR}"
  python3 -m unittest -q backend/tests/test_hybrid_v1_geometry_merge_policy.py
)

echo "[smoke] homepage 200"
HOME_CODE="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/)"
if [[ "${HOME_CODE}" != "200" ]]; then
  echo "[smoke] homepage failed: http=${HOME_CODE}"
  exit 1
fi

echo "[smoke] backend health 200"
API_CODE="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health || true)"
if [[ "${API_CODE}" != "200" ]]; then
  echo "[smoke] backend health failed: http=${API_CODE}"
  exit 1
fi

echo "SMOKE PASS"
