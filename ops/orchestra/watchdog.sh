#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="${ROOT_DIR}:${PATH}"
BASE_URL="${BASE_URL:-http://localhost:7010}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/workspace/ops/orchestra/docker-compose.yml}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-60}"

while true; do
  if ! curl -fsS "${BASE_URL}/state" >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" restart orchestrator litellm autopilot >/dev/null 2>&1 || true
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
