#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:7010}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/workspace/ops/orchestra/docker-compose.yml}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-60}"

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

while true; do
  if ! curl -fsS "${BASE_URL}/state" >/dev/null 2>&1; then
    compose_cmd -f "${COMPOSE_FILE}" restart orchestrator litellm autopilot stellai >/dev/null 2>&1 || true
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
