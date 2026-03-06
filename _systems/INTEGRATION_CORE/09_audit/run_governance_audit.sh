#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace/_systems"
AUDIT_DIR="${ROOT}/audit"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT="${AUDIT_DIR}/governance_audit_${TS//[:]/_}.md"

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    echo "- OK: $path" >> "$OUT"
  else
    echo "- FAIL: $path" >> "$OUT"
  fi
}

mkdir -p "$AUDIT_DIR"
{
  echo "# Governance Audit"
  echo
  echo "Generated: $TS"
  echo
  echo "## Manifest Presence"
} > "$OUT"

check_file "${ROOT}/STELL_CORE/ACTIVE_STELL_MANIFEST.json"
check_file "${ROOT}/ORCHESTRA_CORE/ACTIVE_ORCHESTRA_MANIFEST.json"
check_file "${ROOT}/STELLCODEX_CORE/ACTIVE_STELLCODEX_MANIFEST.json"
check_file "${ROOT}/INTEGRATION_CORE/ACTIVE_INTEGRATION_MANIFEST.json"
check_file "${ROOT}/INFRA_CORE/INFRA_CONNECTION_MANIFEST.json"

{
  echo
  echo "## Guardrail Inputs"
} >> "$OUT"
check_file "${ROOT}/audit/secret_exposure_report.md"
check_file "${ROOT}/audit/system_inventory.json"
check_file "${ROOT}/audit/final_system_state.md"

echo "governance_audit_report=$OUT"
