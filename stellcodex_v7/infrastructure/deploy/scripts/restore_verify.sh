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

RESTORE_DB="stellcodex_restore_check"
OUT_FILE="${EVIDENCE_DIR}/restore_verify.txt"

{
  echo "[restore] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "dump_file=${DUMP_FILE}"
  compose exec -T postgres psql -U stellcodex -d postgres -c "DROP DATABASE IF EXISTS ${RESTORE_DB};"
  compose exec -T postgres psql -U stellcodex -d postgres -c "CREATE DATABASE ${RESTORE_DB};"
} > "${OUT_FILE}"

cat "${DUMP_FILE}" | compose exec -T postgres pg_restore -U stellcodex -d "${RESTORE_DB}" --no-owner --no-privileges

{
  echo
  echo "-- restored table counts"
  compose exec -T postgres psql -U stellcodex -d "${RESTORE_DB}" -P pager=off -c "SELECT 'uploaded_files' AS table, COUNT(*) FROM uploaded_files UNION ALL SELECT 'orchestrator_sessions', COUNT(*) FROM orchestrator_sessions UNION ALL SELECT 'rule_configs', COUNT(*) FROM rule_configs UNION ALL SELECT 'audit_events', COUNT(*) FROM audit_events;"
} >> "${OUT_FILE}"

RESTORED_FILES="$(compose exec -T postgres psql -U stellcodex -d "${RESTORE_DB}" -Atc "SELECT COUNT(*) FROM uploaded_files;")"
if [[ -z "${RESTORED_FILES}" ]]; then
  echo "restore verification failed: no count returned" >&2
  exit 1
fi
if (( RESTORED_FILES < 1 )); then
  echo "restore verification failed: uploaded_files count is ${RESTORED_FILES}" >&2
  exit 1
fi

{
  compose exec -T postgres psql -U stellcodex -d postgres -c "DROP DATABASE IF EXISTS ${RESTORE_DB};"
  echo "[restore] passed"
} >> "${OUT_FILE}"
