#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/infrastructure/deploy/docker-compose.local.yml}"
API_ORIGIN="${API_ORIGIN:-http://localhost:18000}"
API_BASE="${API_BASE:-${API_ORIGIN}/api/v1}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-$(dirname "${COMPOSE_FILE}")/.env}"
DEFAULT_EVIDENCE_ROOT="${ROOT_DIR}/evidence"
if [[ -d "/root/workspace" ]]; then
  DEFAULT_EVIDENCE_ROOT="/root/workspace/evidence"
fi
EVIDENCE_ROOT="${EVIDENCE_ROOT:-${DEFAULT_EVIDENCE_ROOT}}"

if [[ -n "${EVIDENCE_DIR:-}" ]]; then
  EVIDENCE_DIR="${EVIDENCE_DIR}"
else
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  EVIDENCE_DIR="${EVIDENCE_ROOT}/v7_gate_${TS}"
fi
mkdir -p "${EVIDENCE_DIR}"

if [[ -f "${COMPOSE_ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${COMPOSE_ENV_FILE}"
  set +a
fi

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" "$@"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" "$@"
    return
  fi
  if [[ -x /root/workspace/ops/orchestra/docker-compose ]]; then
    /root/workspace/ops/orchestra/docker-compose -f "${COMPOSE_FILE}" "$@"
    return
  fi
  echo "missing docker compose implementation" >&2
  return 127
}

compose_container_id() {
  local service="$1"
  local container_id=""
  local project_name

  container_id="$(compose ps -q "${service}" 2>/dev/null | head -n1 || true)"
  if [[ -n "${container_id}" ]]; then
    printf '%s\n' "${container_id}"
    return 0
  fi

  project_name="$(basename "$(dirname "${COMPOSE_FILE}")")"
  container_id="$(docker ps \
    --filter "label=com.docker.compose.project=${project_name}" \
    --filter "label=com.docker.compose.service=${service}" \
    --format '{{.ID}}' | head -n1)"
  if [[ -n "${container_id}" ]]; then
    printf '%s\n' "${container_id}"
    return 0
  fi

  echo "compose service container not found: ${service}" >&2
  return 1
}

compose_exec() {
  local service="$1"
  shift
  local container_id
  container_id="$(compose_container_id "${service}")" || return 1
  docker exec "${container_id}" "$@"
}

compose_exec_i() {
  local service="$1"
  shift
  local container_id
  container_id="$(compose_container_id "${service}")" || return 1
  docker exec -i "${container_id}" "$@"
}

require_cmd() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "missing required command: ${name}" >&2
    exit 1
  fi
}

wait_backend() {
  local retries="${1:-120}"
  local sleep_seconds="${2:-2}"
  local attempt=0

  until curl -fsS "${API_BASE}/health" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if (( attempt >= retries )); then
      echo "backend health check failed after ${attempt} attempts" >&2
      return 1
    fi
    sleep "${sleep_seconds}"
  done
}

write_json_pretty() {
  local src="$1"
  local dst="$2"
  if command -v jq >/dev/null 2>&1; then
    if jq . "${src}" > "${dst}" 2>/dev/null; then
      return 0
    fi
  fi
  cp "${src}" "${dst}"
}

export SCRIPT_DIR ROOT_DIR COMPOSE_FILE COMPOSE_ENV_FILE API_ORIGIN API_BASE EVIDENCE_ROOT EVIDENCE_DIR
