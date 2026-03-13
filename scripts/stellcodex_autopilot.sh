#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/root/workspace"
MODE="${1:-daily}"
shift || true

source "${ROOT_DIR}/scripts/stellcodex_lock.sh"

if ! stellcodex_acquire_lock "autopilot_${MODE}" 1; then
  echo "AUTOPILOT_BUSY mode=${MODE}" >&2
  exit 75
fi

python3 "${ROOT_DIR}/scripts/stellcodex_autopilot.py" "${MODE}" "$@"
