#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace"
SRC="${ROOT}/_truth"
REMOTE_BASE="${1:-gdrive:stellcodex}"
REMOTE_TRUTH="${REMOTE_BASE}/01_truth"
REPORT_DIR="${SRC}/12_reports"
mkdir -p "${REPORT_DIR}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="${REPORT_DIR}/truth_sync_${TS}.log"

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is required" >&2
  exit 1
fi

{
  echo "[truth-sync] started ${TS}"
  echo "src=${SRC}"
  echo "dst=${REMOTE_TRUTH}"
  rclone mkdir "${REMOTE_TRUTH}"
  rclone sync "${SRC}" "${REMOTE_TRUTH}" --checksum --create-empty-src-dirs
  rclone check "${SRC}" "${REMOTE_TRUTH}" --checksum --one-way
  echo "[truth-sync] PASS"
} | tee "${LOG_FILE}"

echo "${LOG_FILE}"

