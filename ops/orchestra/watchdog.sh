#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="${ROOT_DIR}:${PATH}"
BASE_URL="${BASE_URL:-http://localhost:7010}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/workspace/ops/orchestra/docker-compose.yml}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-60}"

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  elif [[ -x "${ROOT_DIR}/docker-compose" ]]; then
    "${ROOT_DIR}/docker-compose" "$@"
  else
    echo "missing docker compose implementation" >&2
    return 127
  fi
}

while true; do
  running="$(docker ps --filter name=orchestra_orchestrator --filter status=running --format '{{.Names}}' 2>/dev/null | head -1)"
  if [[ -z "${running}" ]]; then
    compose_cmd -f "${COMPOSE_FILE}" up -d orchestrator litellm autopilot >/dev/null 2>&1 || true
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
