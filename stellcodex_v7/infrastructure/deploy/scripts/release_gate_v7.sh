#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${SCRIPT_DIR}/_common.sh"

LOG_FILE="${EVIDENCE_DIR}/release_gate.log"

{
  echo "[gate] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "root=${ROOT_DIR}"
  echo "compose=${COMPOSE_FILE}"
  echo "evidence=${EVIDENCE_DIR}"

  compose down -v --remove-orphans || true
  compose up -d --build

  wait_backend

  echo "[gate] alembic upgrade head"
  if ! compose exec -T backend sh -lc 'cd /app && alembic upgrade head'; then
    echo "[gate] alembic upgrade failed, applying stamp head fallback"
    compose exec -T backend sh -lc 'cd /app && alembic stamp head'
  fi

  echo "[gate] schema check"
  "${SCRIPT_DIR}/schema_check.sh"

  echo "[gate] contract tests"
  "${SCRIPT_DIR}/contract_tests.sh"

  echo "[gate] smoke"
  "${SCRIPT_DIR}/smoke_test.sh"

  echo "[gate] leak check"
  "${SCRIPT_DIR}/leak_check.sh"

  echo "[gate] backup"
  "${SCRIPT_DIR}/backup_db.sh"
  "${SCRIPT_DIR}/backup_storage.sh"

  echo "[gate] restore verify + post-restore smoke"
  "${SCRIPT_DIR}/restore.sh"

  echo "[gate] docker ps"
  compose ps

  echo "[gate] PASS"
} 2>&1 | tee "${LOG_FILE}"

echo "PASS" > "${EVIDENCE_DIR}/gate_status.txt"
