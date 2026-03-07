#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_WRAPPER="/root/workspace/scripts/docker-compose-safe.sh"

exec bash "${WORKSPACE_WRAPPER}" -f "${SCRIPT_DIR}/docker-compose.yml" "$@"
