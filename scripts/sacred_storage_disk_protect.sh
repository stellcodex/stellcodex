#!/usr/bin/env bash
set -euo pipefail

THRESHOLD="${1:-70}"
REMOTE_BASE="${2:-gdrive:stellcodex}"
USE_PCT="$(df --output=pcent / | tail -n1 | tr -dc '0-9')"

echo "disk_use_percent=${USE_PCT}"
if (( USE_PCT < THRESHOLD )); then
  echo "status=ok threshold=${THRESHOLD}"
  exit 0
fi

echo "status=archive_required threshold=${THRESHOLD}"
"/root/workspace/scripts/sacred_storage_migrate.sh" "${REMOTE_BASE}"

