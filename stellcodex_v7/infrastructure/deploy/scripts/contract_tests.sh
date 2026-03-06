#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_cmd curl
wait_backend

LOG_FILE="${EVIDENCE_DIR}/contract_tests.log"

{
  echo "[contract] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  compose exec -T backend sh -lc 'cd /app && python -m unittest -v \
    tests.test_guest_token_identity \
    tests.test_format_registry_contract \
    tests.test_hybrid_v1_geometry_merge_policy \
    tests.test_master_contract_routes \
    tests.test_upload_contracts \
    tests.test_public_contract_leaks \
    tests.test_orchestrator_core'
  echo "[contract] passed"
} 2>&1 | tee "${LOG_FILE}"
