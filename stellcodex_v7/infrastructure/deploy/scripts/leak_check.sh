#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

TARGET_DIR="${EVIDENCE_DIR}/smoke"
OUT_FILE="${EVIDENCE_DIR}/leak_check.txt"
mkdir -p "${TARGET_DIR}"

BANNED=(
  "storage_key"
  "revision_id"
  "s3://"
  "r2://"
  "\"bucket\""
  "'bucket'"
)

{
  echo "[leak-check] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "target=${TARGET_DIR}"
} > "${OUT_FILE}"

for pattern in "${BANNED[@]}"; do
  if rg -n -i -F "${pattern}" "${TARGET_DIR}"/*.json >> "${OUT_FILE}" 2>/dev/null; then
    echo "[leak-check] failed: banned token found (${pattern})" | tee -a "${OUT_FILE}" >&2
    exit 1
  fi
  echo "[leak-check] clean pattern=${pattern}" >> "${OUT_FILE}"
done

echo "[leak-check] passed" | tee -a "${OUT_FILE}"
