#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${SCRIPT_DIR}/_common.sh"
LOCK_HELPER="${ROOT_DIR}/scripts/stellcodex_lock.sh"
if [[ ! -f "${LOCK_HELPER}" && -f "/root/workspace/scripts/stellcodex_lock.sh" ]]; then
  LOCK_HELPER="/root/workspace/scripts/stellcodex_lock.sh"
fi
source "${LOCK_HELPER}"

LOG_FILE="${EVIDENCE_DIR}/release_gate.log"
STATUS_FILE="${EVIDENCE_DIR}/gate_status.txt"
RELEASE_GATE_LOCK_WAIT_SECONDS="${RELEASE_GATE_LOCK_WAIT_SECONDS:-0}"
RELEASE_GATE_BUILD="${RELEASE_GATE_BUILD:-auto}"
RELEASE_GATE_RESET_STACK="${RELEASE_GATE_RESET_STACK:-0}"
RELEASE_GATE_DROP_VOLUMES="${RELEASE_GATE_DROP_VOLUMES:-0}"

is_true() {
  case "${1:-0}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

should_build_images() {
  local project_name backend_image worker_image
  project_name="$(basename "$(dirname "${COMPOSE_FILE}")")"
  backend_image="${project_name}_backend:latest"
  worker_image="${project_name}_worker:latest"

  if [[ "${RELEASE_GATE_BUILD}" == "auto" ]]; then
    docker image inspect "${backend_image}" >/dev/null 2>&1 || return 0
    docker image inspect "${worker_image}" >/dev/null 2>&1 || return 0
    return 1
  fi

  is_true "${RELEASE_GATE_BUILD}"
}

echo "RUNNING" > "${STATUS_FILE}"

on_exit() {
  local status=$?
  if (( status != 0 )); then
    echo "FAIL" > "${STATUS_FILE}"
  fi
}
trap on_exit EXIT

if ! stellcodex_acquire_lock "heavy_ops" "${RELEASE_GATE_LOCK_WAIT_SECONDS}"; then
  {
    echo "[gate] skipped: another heavy operation already holds the lock"
    echo "[gate] lock=/root/workspace/_runtime/locks/heavy_ops.lock"
  } | tee -a "${LOG_FILE}"
  echo "SKIPPED_LOCKED" > "${STATUS_FILE}"
  exit 0
fi

{
  echo "[gate] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "root=${ROOT_DIR}"
  echo "compose=${COMPOSE_FILE}"
  echo "evidence=${EVIDENCE_DIR}"
  echo "build_mode=${RELEASE_GATE_BUILD}"
  echo "reset_stack=${RELEASE_GATE_RESET_STACK}"
  echo "drop_volumes=${RELEASE_GATE_DROP_VOLUMES}"

  if is_true "${RELEASE_GATE_RESET_STACK}"; then
    down_args=(down --remove-orphans)
    if is_true "${RELEASE_GATE_DROP_VOLUMES}"; then
      down_args+=(-v)
    fi
    compose "${down_args[@]}" || true
  fi

  up_args=(up -d)
  if should_build_images; then
    up_args+=(--build)
  fi
  compose "${up_args[@]}"

  wait_backend

  echo "[gate] alembic upgrade head"
  if ! compose_exec backend sh -lc 'cd /app && alembic upgrade head'; then
    echo "[gate] alembic upgrade failed, applying stamp head fallback"
    compose_exec backend sh -lc 'cd /app && alembic stamp head'
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

  if [[ "${DRIVE_EXPORT_REQUIRED:-0}" == "1" ]]; then
    echo "[gate] drive export"
    "${SCRIPT_DIR}/drive_export.sh"
  fi

  echo "[gate] docker ps"
  compose ps

  echo "[gate] PASS"
} 2>&1 | tee "${LOG_FILE}"

echo "PASS" > "${STATUS_FILE}"
