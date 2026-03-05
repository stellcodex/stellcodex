#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-start}"
JOBS_ROOT="${2:-/root/workspace/_jobs}"
LOG_DIR="${JOBS_ROOT}/logs"
PID_FILE="${LOG_DIR}/watchdog.pid"
BASE_URL="${BASE_URL:-http://localhost:7010}"

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

wait_state() {
  local tries="${1:-60}"
  local sleep_s="${2:-2}"
  local i
  for ((i=1; i<=tries; i++)); do
    if curl -fsS "${BASE_URL}/state" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_s}"
  done
  return 1
}

start_watchdog() {
  mkdir -p "${LOG_DIR}"
  if [[ -f "${PID_FILE}" ]]; then
    local old_pid
    old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
      return 0
    fi
  fi
  nohup "${ROOT_DIR}/watchdog.sh" >"${LOG_DIR}/watchdog.log" 2>&1 &
  echo "$!" >"${PID_FILE}"
}

stop_watchdog() {
  if [[ -f "${PID_FILE}" ]]; then
    local pid
    pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${pid}" ]]; then
      kill "${pid}" >/dev/null 2>&1 || true
    fi
    rm -f "${PID_FILE}"
  fi
}

ensure_jobs() {
  mkdir -p \
    "${JOBS_ROOT}/inbox" \
    "${JOBS_ROOT}/done" \
    "${JOBS_ROOT}/failed" \
    "${JOBS_ROOT}/deferred" \
    "${JOBS_ROOT}/output" \
    "${JOBS_ROOT}/logs" \
    "${JOBS_ROOT}/backups"
}

case "${ACTION}" in
  start)
    ensure_jobs
    "${ROOT_DIR}/preflight.sh" "${JOBS_ROOT}"
    "${ROOT_DIR}/backup.sh" "${JOBS_ROOT}"

    compose_cmd -f "${ROOT_DIR}/docker-compose.yml" up -d --build litellm orchestrator autopilot stellai ollama

    wait_state 60 2 || true
    start_watchdog
    echo "AUTOPILOT_STARTED jobs_root=${JOBS_ROOT}"
    ;;
  stop)
    stop_watchdog
    compose_cmd -f "${ROOT_DIR}/docker-compose.yml" stop autopilot stellai orchestrator litellm ollama || true
    echo "AUTOPILOT_STOPPED"
    ;;
  restart)
    "${ROOT_DIR}/autopilot.sh" stop "${JOBS_ROOT}"
    "${ROOT_DIR}/autopilot.sh" start "${JOBS_ROOT}"
    ;;
  status)
    compose_cmd -f "${ROOT_DIR}/docker-compose.yml" ps
    if [[ -f "${PID_FILE}" ]]; then
      echo "watchdog_pid=$(cat "${PID_FILE}")"
    else
      echo "watchdog_pid=none"
    fi
    ;;
  *)
    echo "Usage: ./autopilot.sh {start|stop|restart|status} [jobs_root]"
    exit 1
    ;;
esac
