#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

BACKUP_DIR="${EVIDENCE_DIR}/backups"
mkdir -p "${BACKUP_DIR}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DAY_STAMP="$(date -u +%Y-%m-%d)"
DUMP_FILE="${BACKUP_DIR}/postgres_${STAMP}.dump"
META_FILE="${BACKUP_DIR}/backup_${STAMP}.txt"
SHA_FILE="${BACKUP_DIR}/postgres_${STAMP}.sha256"

{
  echo "[backup] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "policy=daily_db_dump"
  echo "day=${DAY_STAMP}"
  echo "dump_file=${DUMP_FILE}"
} | tee "${META_FILE}"

compose exec -T postgres pg_dump -U stellcodex -d stellcodex -Fc > "${DUMP_FILE}"
sha256sum "${DUMP_FILE}" | tee "${SHA_FILE}" | tee -a "${META_FILE}"

{
  echo
  echo "-- table counts"
  compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c "SELECT 'uploaded_files' AS table, COUNT(*) FROM uploaded_files UNION ALL SELECT 'orchestrator_sessions', COUNT(*) FROM orchestrator_sessions UNION ALL SELECT 'rule_configs', COUNT(*) FROM rule_configs UNION ALL SELECT 'audit_events', COUNT(*) FROM audit_events;"
  echo "[backup] completed"
} >> "${META_FILE}"

echo "${DUMP_FILE}" > "${EVIDENCE_DIR}/latest_backup_path.txt"
echo "${SHA_FILE}" > "${EVIDENCE_DIR}/latest_backup_sha_path.txt"
