#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 <local-file> <remote-dir> [latest-name]" >&2
  exit 2
fi

LOCAL_FILE="$1"
REMOTE_DIR="$2"
LATEST_NAME="${3:-$(basename "$LOCAL_FILE")}"

if [[ ! -f "${LOCAL_FILE}" ]]; then
  echo "local file not found: ${LOCAL_FILE}" >&2
  exit 1
fi

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is required" >&2
  exit 1
fi

SHA256="$(sha256sum "${LOCAL_FILE}" | awk '{print $1}')"
SIZE_BYTES="$(stat -c %s "${LOCAL_FILE}")"

if [[ "${LATEST_NAME}" == *.* ]]; then
  STEM="${LATEST_NAME%.*}"
  EXT=".${LATEST_NAME##*.}"
else
  STEM="${LATEST_NAME}"
  EXT=""
fi

ARCHIVE_NAME="${STEM}.${SHA256}${EXT}"
ARCHIVE_DIR="${REMOTE_DIR}/archive"
CURRENT_DIR="${REMOTE_DIR}/current"
ARCHIVE_REMOTE="${ARCHIVE_DIR}/${ARCHIVE_NAME}"
CURRENT_REMOTE="${CURRENT_DIR}/${LATEST_NAME}"

rclone mkdir "${ARCHIVE_DIR}" >/dev/null
rclone mkdir "${CURRENT_DIR}" >/dev/null

ARCHIVE_STATUS="uploaded"
if rclone lsf "${ARCHIVE_DIR}" --max-depth 1 | grep -Fx "${ARCHIVE_NAME}" >/dev/null 2>&1; then
  ARCHIVE_STATUS="skipped_duplicate"
else
  rclone copyto "${LOCAL_FILE}" "${ARCHIVE_REMOTE}"
fi

rclone copyto "${LOCAL_FILE}" "${CURRENT_REMOTE}"

CURRENT_PRESENT="false"
if rclone lsf "${CURRENT_DIR}" --max-depth 1 | grep -Fx "${LATEST_NAME}" >/dev/null 2>&1; then
  CURRENT_PRESENT="true"
fi

python3 - <<'PY' "${LOCAL_FILE}" "${REMOTE_DIR}" "${LATEST_NAME}" "${SHA256}" "${SIZE_BYTES}" "${ARCHIVE_STATUS}" "${CURRENT_PRESENT}"
import json
import sys

payload = {
    "local_file": sys.argv[1],
    "remote_dir": sys.argv[2],
    "latest_name": sys.argv[3],
    "sha256": sys.argv[4],
    "size_bytes": int(sys.argv[5]),
    "archive_status": sys.argv[6],
    "current_present": sys.argv[7] == "true",
}
print(json.dumps(payload, indent=2, ensure_ascii=True))
PY
