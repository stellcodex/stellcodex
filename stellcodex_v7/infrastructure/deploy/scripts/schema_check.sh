#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

OUT_FILE="${EVIDENCE_DIR}/db_schema_check.txt"

{
  echo "[schema] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "-- tables"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c "\dt" || true
  echo
  echo "-- critical columns"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT table_name, column_name, is_nullable, data_type, udt_name FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('uploaded_files','orchestrator_sessions','rule_configs') ORDER BY table_name, ordinal_position;"
  echo
  echo "-- decision_json null check"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT COUNT(*) AS missing_decision_json FROM uploaded_files WHERE decision_json IS NULL;"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT COUNT(*) AS missing_orchestrator_decision_json FROM orchestrator_sessions WHERE decision_json IS NULL;"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT COUNT(*) AS missing_v7_fields FROM orchestrator_sessions WHERE state IS NULL OR rule_version IS NULL OR mode IS NULL OR confidence IS NULL;"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT COUNT(*) AS missing_tenant_id FROM uploaded_files WHERE tenant_id IS NULL;"
  echo
  echo "-- rule config keys"
  compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
    "SELECT key, enabled FROM rule_configs ORDER BY key;"
  echo "[schema] completed"
} 2>&1 | tee "${OUT_FILE}"

MISSING_COUNT="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM uploaded_files WHERE decision_json IS NULL;")"
if [[ "${MISSING_COUNT}" != "0" ]]; then
  echo "decision_json NOT NULL check failed (missing=${MISSING_COUNT})" >&2
  exit 1
fi

MISSING_SESSION_DECISION="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM orchestrator_sessions WHERE decision_json IS NULL;")"
if [[ "${MISSING_SESSION_DECISION}" != "0" ]]; then
  echo "orchestrator_sessions decision_json NOT NULL check failed (missing=${MISSING_SESSION_DECISION})" >&2
  exit 1
fi

MISSING_V7_FIELDS="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM orchestrator_sessions WHERE state IS NULL OR rule_version IS NULL OR mode IS NULL OR confidence IS NULL;")"
if [[ "${MISSING_V7_FIELDS}" != "0" ]]; then
  echo "orchestrator_sessions V7 columns backfill check failed (missing=${MISSING_V7_FIELDS})" >&2
  exit 1
fi

MISSING_TENANT_ID="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM uploaded_files WHERE tenant_id IS NULL;")"
if [[ "${MISSING_TENANT_ID}" != "0" ]]; then
  echo "uploaded_files tenant_id check failed (missing=${MISSING_TENANT_ID})" >&2
  exit 1
fi
