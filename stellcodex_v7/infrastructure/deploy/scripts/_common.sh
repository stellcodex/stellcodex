#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/infrastructure/deploy/docker-compose.local.yml}"
API_ORIGIN="${API_ORIGIN:-http://localhost:18000}"
API_BASE="${API_BASE:-${API_ORIGIN}/api/v1}"
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

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" "$@"
    return
  fi
  if [[ -x /root/workspace/ops/orchestra/docker-compose ]]; then
    /root/workspace/ops/orchestra/docker-compose -f "${COMPOSE_FILE}" "$@"
    return
  fi
  docker-compose -f "${COMPOSE_FILE}" "$@"
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

export SCRIPT_DIR ROOT_DIR COMPOSE_FILE API_ORIGIN API_BASE EVIDENCE_ROOT EVIDENCE_DIR
