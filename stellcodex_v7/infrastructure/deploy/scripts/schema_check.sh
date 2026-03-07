#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

OUT_FILE="${EVIDENCE_DIR}/db_schema_check.txt"

{
  echo "[schema] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "-- tables"
  compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c "\dt" || true
  echo
  echo "-- critical columns"
  compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT table_name, column_name, is_nullable, data_type, udt_name FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('uploaded_files','orchestrator_sessions','rule_configs') ORDER BY table_name, ordinal_position;"
  echo
  echo "-- decision_json null check"
  compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT COUNT(*) AS missing_decision_json FROM uploaded_files WHERE decision_json IS NULL;"
  echo
  echo "-- rule config keys"
  compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT key, enabled FROM rule_configs ORDER BY key;"
  echo "[schema] completed"
} 2>&1 | tee "${OUT_FILE}"

MISSING_COUNT="$(compose exec -T postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM uploaded_files WHERE decision_json IS NULL;")"
if [[ "${MISSING_COUNT}" != "0" ]]; then
  echo "decision_json NOT NULL check failed (missing=${MISSING_COUNT})" >&2
  exit 1
fi
