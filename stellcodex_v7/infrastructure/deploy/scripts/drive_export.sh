#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_cmd rclone

UPLOAD_HELPER="${ROOT_DIR}/scripts/drive_dedup_upload.sh"
if [[ ! -x "${UPLOAD_HELPER}" && -x "/root/workspace/scripts/drive_dedup_upload.sh" ]]; then
  UPLOAD_HELPER="/root/workspace/scripts/drive_dedup_upload.sh"
fi
if [[ ! -x "${UPLOAD_HELPER}" ]]; then
  echo "drive upload helper missing or not executable: ${UPLOAD_HELPER}" >&2
  exit 1
fi

if [[ ! -f "${EVIDENCE_DIR}/latest_backup_path.txt" ]]; then
  echo "missing DB backup reference: ${EVIDENCE_DIR}/latest_backup_path.txt" >&2
  exit 1
fi

REMOTE_BASE="${DRIVE_EXPORT_REMOTE_BASE:-gdrive:stellcodex/evidence/executions/$(date -u +%Y%m%d)}"
RUN_DIR="${EVIDENCE_DIR}/drive_export"
STATUS_FILE="${EVIDENCE_DIR}/drive_export_status.txt"
MANIFEST_JSON="${EVIDENCE_DIR}/drive_export_manifest.json"

mkdir -p "${RUN_DIR}"

DB_DUMP_PATH="$(cat "${EVIDENCE_DIR}/latest_backup_path.txt")"
DB_SHA_PATH=""
STORAGE_DIR=""
STORAGE_ARCHIVE_PATH=""

if [[ -f "${EVIDENCE_DIR}/latest_backup_sha_path.txt" ]]; then
  DB_SHA_PATH="$(cat "${EVIDENCE_DIR}/latest_backup_sha_path.txt")"
fi
if [[ -f "${EVIDENCE_DIR}/latest_storage_backup_dir.txt" ]]; then
  STORAGE_DIR="$(cat "${EVIDENCE_DIR}/latest_storage_backup_dir.txt")"
fi

if [[ ! -f "${DB_DUMP_PATH}" ]]; then
  echo "missing DB dump: ${DB_DUMP_PATH}" >&2
  exit 1
fi

if [[ -n "${STORAGE_DIR}" && -d "${STORAGE_DIR}" ]]; then
  STORAGE_ARCHIVE_PATH="${RUN_DIR}/$(basename "${STORAGE_DIR}").tar.gz"
  tar -C "$(dirname "${STORAGE_DIR}")" -czf "${STORAGE_ARCHIVE_PATH}" "$(basename "${STORAGE_DIR}")"
fi

DB_DUMP_SUMMARY="${RUN_DIR}/db_dump_upload.json"
DB_SHA_SUMMARY="${RUN_DIR}/db_sha_upload.json"
STORAGE_SUMMARY="${RUN_DIR}/storage_upload.json"

"${UPLOAD_HELPER}" "${DB_DUMP_PATH}" "${REMOTE_BASE}/db" "$(basename "${DB_DUMP_PATH}")" > "${DB_DUMP_SUMMARY}"
if [[ -n "${DB_SHA_PATH}" && -f "${DB_SHA_PATH}" ]]; then
  "${UPLOAD_HELPER}" "${DB_SHA_PATH}" "${REMOTE_BASE}/db" "$(basename "${DB_SHA_PATH}")" > "${DB_SHA_SUMMARY}"
fi
if [[ -n "${STORAGE_ARCHIVE_PATH}" && -f "${STORAGE_ARCHIVE_PATH}" ]]; then
  "${UPLOAD_HELPER}" "${STORAGE_ARCHIVE_PATH}" "${REMOTE_BASE}/storage" "$(basename "${STORAGE_ARCHIVE_PATH}")" > "${STORAGE_SUMMARY}"
fi

rm -f "${DB_DUMP_PATH}"
if [[ -n "${STORAGE_ARCHIVE_PATH}" && -f "${STORAGE_ARCHIVE_PATH}" ]]; then
  rm -f "${STORAGE_ARCHIVE_PATH}"
fi
if [[ -n "${STORAGE_DIR}" && -d "${STORAGE_DIR}" ]]; then
  rm -rf "${STORAGE_DIR}"
fi

python3 - <<'PY' "${MANIFEST_JSON}" "${REMOTE_BASE}" "${DB_DUMP_SUMMARY}" "${DB_SHA_SUMMARY}" "${STORAGE_SUMMARY}" "${DB_DUMP_PATH}" "${DB_SHA_PATH}" "${STORAGE_DIR}"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def load_summary(path_str: str) -> Optional[dict]:
    path = Path(path_str)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


manifest_path = Path(sys.argv[1])
remote_base = sys.argv[2]
db_dump_summary = load_summary(sys.argv[3])
db_sha_summary = load_summary(sys.argv[4])
storage_summary = load_summary(sys.argv[5])
db_dump_path = sys.argv[6]
db_sha_path = sys.argv[7]
storage_dir = sys.argv[8]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "remote_base": remote_base,
    "db_dump": {
        "local_path": db_dump_path,
        "local_deleted": not Path(db_dump_path).exists(),
        "upload": db_dump_summary,
    },
    "db_sha256": {
        "local_path": db_sha_path or None,
        "local_deleted": (not db_sha_path) or (not Path(db_sha_path).exists()),
        "upload": db_sha_summary,
    },
    "storage_snapshot": {
        "local_path": storage_dir or None,
        "local_deleted": (not storage_dir) or (not Path(storage_dir).exists()),
        "upload": storage_summary,
    },
}
manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
PY

echo "PASS" > "${STATUS_FILE}"
echo "${MANIFEST_JSON}"
