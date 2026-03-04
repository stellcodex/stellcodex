#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/evidence"
OUT_FILE="${EVIDENCE_DIR}/weekly_restore_gate_output.txt"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"
DB_CONTAINER="${DB_CONTAINER:-stellcodex-postgres}"
DB_USER="${DB_USER:-stellcodex}"
DB_NAME="${DB_NAME:-stellcodex}"
RESTORE_DB_NAME="${RESTORE_DB_NAME:-stellcodex_restore_probe}"
RUN_RELEASE_GATE="${RUN_RELEASE_GATE:-1}"
RUN_SMOKE_GATE="${RUN_SMOKE_GATE:-0}"
KEEP_RESTORE_DB="${KEEP_RESTORE_DB:-0}"
DUMP_FILE="${DUMP_FILE:-}"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${OUT_FILE}") 2>&1

fail() {
  echo "[FAIL] $1"
  echo "RESULT=FAIL"
  echo "EVIDENCE=${OUT_FILE}"
  exit 1
}

pass() {
  echo "[PASS] $1"
}

find_latest_dump() {
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name "db_${DB_NAME}_*.sql.gz" | sort | tail -n 1
}

cleanup_restore_db() {
  if [[ "${KEEP_RESTORE_DB}" == "1" ]]; then
    return
  fi
  docker exec "${DB_CONTAINER}" sh -lc \
    "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; dropdb --if-exists -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\"" >/dev/null 2>&1 || true
}

trap cleanup_restore_db EXIT

echo "# Weekly restore gate"
date -Iseconds
echo "backup_dir=${BACKUP_DIR}"
echo "db_container=${DB_CONTAINER}"
echo "restore_db_name=${RESTORE_DB_NAME}"

command -v docker >/dev/null 2>&1 || fail "docker is required"
docker inspect "${DB_CONTAINER}" >/dev/null 2>&1 || fail "db container not found: ${DB_CONTAINER}"

if [[ -z "${DUMP_FILE}" ]]; then
  DUMP_FILE="$(find_latest_dump)"
fi
[[ -n "${DUMP_FILE}" ]] || fail "no dump found in ${BACKUP_DIR}"
[[ -f "${DUMP_FILE}" ]] || fail "dump file missing: ${DUMP_FILE}"
pass "selected dump ${DUMP_FILE}"

echo "[1/4] recreate restore database"
docker exec "${DB_CONTAINER}" sh -lc \
  "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; dropdb --if-exists -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\" && createdb -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\"" \
  || fail "failed to recreate restore database"
pass "restore database recreated"

echo "[2/4] restore dump into temporary database"
gzip -dc "${DUMP_FILE}" | docker exec -i "${DB_CONTAINER}" sh -lc \
  "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; psql -v ON_ERROR_STOP=1 -U \"${DB_USER}\" -d \"${RESTORE_DB_NAME}\"" \
  >/dev/null || fail "restore into ${RESTORE_DB_NAME} failed"
pass "dump restored"

echo "[3/4] restored database sanity"
TABLE_COUNT="$(docker exec "${DB_CONTAINER}" sh -lc \
  "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; psql -At -U \"${DB_USER}\" -d \"${RESTORE_DB_NAME}\" -c \"select count(*) from information_schema.tables where table_schema='public';\"")"
[[ -n "${TABLE_COUNT}" ]] || fail "sanity query returned empty result"
[[ "${TABLE_COUNT}" -gt 0 ]] || fail "restored database has no public tables"
pass "restored database sanity ok (public_tables=${TABLE_COUNT})"

echo "[4/4] application gates"
if [[ "${RUN_RELEASE_GATE}" == "1" ]]; then
  "${ROOT_DIR}/scripts/release_gate.sh" || fail "release_gate.sh failed"
  pass "release gate ok"
fi
if [[ "${RUN_SMOKE_GATE}" == "1" ]]; then
  "${ROOT_DIR}/scripts/smoke_gate.sh" || fail "smoke_gate.sh failed"
  pass "smoke gate ok"
fi

echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
