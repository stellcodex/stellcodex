#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

if [[ -n "${1:-}" ]]; then
  DUMP_FILE="$1"
else
  if [[ ! -f "${EVIDENCE_DIR}/latest_backup_path.txt" ]]; then
    echo "backup path not found: ${EVIDENCE_DIR}/latest_backup_path.txt" >&2
    exit 1
  fi
  DUMP_FILE="$(cat "${EVIDENCE_DIR}/latest_backup_path.txt")"
fi

if [[ ! -f "${DUMP_FILE}" ]]; then
  echo "backup dump not found: ${DUMP_FILE}" >&2
  exit 1
fi

if [[ -f "${EVIDENCE_DIR}/latest_backup_sha_path.txt" ]]; then
  SHA_FILE="$(cat "${EVIDENCE_DIR}/latest_backup_sha_path.txt")"
  if [[ -f "${SHA_FILE}" ]]; then
    sha256sum -c "${SHA_FILE}"
  fi
fi

RESTORE_DB="${RESTORE_DB_NAME:-stellcodex_restore_check}"
OUT_FILE="${EVIDENCE_DIR}/restore.txt"

{
  echo "[restore] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "dump_file=${DUMP_FILE}"
  echo "restore_db=${RESTORE_DB}"
  compose exec -T postgres psql -U stellcodex -d postgres -c "DROP DATABASE IF EXISTS ${RESTORE_DB};"
  compose exec -T postgres psql -U stellcodex -d postgres -c "CREATE DATABASE ${RESTORE_DB};"
} | tee "${OUT_FILE}"

cat "${DUMP_FILE}" | compose exec -T postgres pg_restore -U stellcodex -d "${RESTORE_DB}" --no-owner --no-privileges

{
  echo
  echo "-- restored table counts"
  compose exec -T postgres psql -U stellcodex -d "${RESTORE_DB}" -P pager=off -c "SELECT 'uploaded_files' AS table, COUNT(*) FROM uploaded_files UNION ALL SELECT 'orchestrator_sessions', COUNT(*) FROM orchestrator_sessions UNION ALL SELECT 'rule_configs', COUNT(*) FROM rule_configs UNION ALL SELECT 'audit_events', COUNT(*) FROM audit_events;"
} | tee -a "${OUT_FILE}"

RESTORED_FILES="$(compose exec -T postgres psql -U stellcodex -d "${RESTORE_DB}" -Atc "SELECT COUNT(*) FROM uploaded_files;")"
if [[ -z "${RESTORED_FILES}" ]]; then
  echo "restore verification failed: no count returned" >&2
  exit 1
fi
if (( RESTORED_FILES < 1 )); then
  echo "restore verification failed: uploaded_files count is ${RESTORED_FILES}" >&2
  exit 1
fi

if [[ -f "${EVIDENCE_DIR}/latest_storage_backup_dir.txt" ]]; then
  STORAGE_DIR="$(cat "${EVIDENCE_DIR}/latest_storage_backup_dir.txt")"
  MANIFEST_FILE="${STORAGE_DIR}/object_manifest.sha256"
  if [[ -f "${MANIFEST_FILE}" ]]; then
    (
      cd "${STORAGE_DIR}/objects"
      sha256sum -c "${MANIFEST_FILE}"
    ) | tee -a "${OUT_FILE}"
  fi
fi

"${SCRIPT_DIR}/smoke_test.sh"

compose exec -T postgres psql -U stellcodex -d postgres -c "DROP DATABASE IF EXISTS ${RESTORE_DB};" >> "${OUT_FILE}"

WEEK_ID="$(date -u +%G-W%V)"
echo "weekly_restore_test=${WEEK_ID}" >> "${OUT_FILE}"
echo "[restore] PASS" | tee -a "${OUT_FILE}"
echo "PASS" > "${EVIDENCE_DIR}/restore_status.txt"
