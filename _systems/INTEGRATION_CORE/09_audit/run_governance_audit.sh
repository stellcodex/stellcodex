#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace/_systems"
REPO="/root/workspace"
AUDIT_DIR="${ROOT}/audit"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT="${AUDIT_DIR}/governance_audit_${TS//[:]/_}.md"
TMP="$(mktemp)"

mkdir -p "$AUDIT_DIR"
touch "$OUT"

PASS=0
FAIL=0

record_check() {
  local name="$1"
  local status="$2"
  local detail="$3"
  if [[ "$status" == "PASS" ]]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
  {
    echo "- ${name}: ${status}"
    echo "  detail: ${detail}"
  } >> "$OUT"
}

require_file() {
  local label="$1"
  local path="$2"
  if [[ -f "$path" ]]; then
    record_check "$label" "PASS" "$path"
  else
    record_check "$label" "FAIL" "missing: $path"
  fi
}

{
  echo "# Governance Audit"
  echo
  echo "Generated: $TS"
  echo
  echo "## Manifest Presence"
} > "$OUT"

require_file "STELL manifest" "${ROOT}/STELL_CORE/ACTIVE_STELL_MANIFEST.json"
require_file "ORCHESTRA manifest" "${ROOT}/ORCHESTRA_CORE/ACTIVE_ORCHESTRA_MANIFEST.json"
require_file "STELLCODEX manifest" "${ROOT}/STELLCODEX_CORE/ACTIVE_STELLCODEX_MANIFEST.json"
require_file "INTEGRATION manifest" "${ROOT}/INTEGRATION_CORE/ACTIVE_INTEGRATION_MANIFEST.json"
require_file "INFRA manifest" "${ROOT}/INFRA_CORE/INFRA_CONNECTION_MANIFEST.json"

{
  echo
  echo "## Guardrails"
} >> "$OUT"

# duplicate prompt detection (exclude backup/archive mirrors to surface active drift)
find "$REPO" \
  \( -path "$REPO/_backups" -o -path "$REPO/audit" -o -path "$REPO/_systems/ARCHIVE_LEGACY" \) -prune -o \
  -type f \( -iname "*prompt*.md" -o -iname "*constitution*.md" \) -printf "%f\n" | \
  sort | uniq -d > "$TMP" || true
if [[ -s "$TMP" ]]; then
  dupes="$(paste -sd', ' "$TMP")"
  record_check "duplicate_prompt_detection" "FAIL" "duplicate filenames: ${dupes}"
else
  record_check "duplicate_prompt_detection" "PASS" "no duplicate prompt/constitution filenames detected"
fi

# manifest authority violation
if grep -Eq '"allowed_flows"' "${ROOT}/INTEGRATION_CORE/ACTIVE_INTEGRATION_MANIFEST.json" && \
   grep -Eq '"audit_trigger_on_violation"[[:space:]]*:[[:space:]]*true' "${ROOT}/INTEGRATION_CORE/ACTIVE_INTEGRATION_MANIFEST.json"; then
  record_check "manifest_authority_violation" "PASS" "integration manifest contains allowed flow boundary and audit trigger"
else
  record_check "manifest_authority_violation" "FAIL" "integration manifest missing required boundary fields"
fi

# secret exposure detection (report presence + non-empty)
if [[ -s "${ROOT}/audit/secret_exposure_report.md" ]]; then
  findings="$(grep -Ec '^- /' "${ROOT}/audit/secret_exposure_report.md" || true)"
  record_check "secret_exposure_detection" "PASS" "secret report present; findings indexed: ${findings}"
else
  record_check "secret_exposure_detection" "FAIL" "secret_exposure_report.md missing or empty"
fi

# backup verification
backup_count="$(find /root/stellcodex_output/backups -maxdepth 1 -type f -name 'backup_*.zip' 2>/dev/null | wc -l | awk '{print $1}')"
if [[ "${backup_count}" -gt 0 ]]; then
  latest_backup="$(ls -1t /root/stellcodex_output/backups/backup_*.zip 2>/dev/null | head -n1)"
  record_check "backup_verification_failure" "PASS" "backups found: ${backup_count}; latest: ${latest_backup}"
else
  record_check "backup_verification_failure" "FAIL" "no backup_*.zip found under /root/stellcodex_output/backups"
fi

# external connector health check
connector_failures=0
if ! git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
  connector_failures=$((connector_failures + 1))
fi
if ! docker exec deploy_redis_1 redis-cli ping >/dev/null 2>&1; then
  connector_failures=$((connector_failures + 1))
fi
if [[ "${connector_failures}" -eq 0 ]]; then
  record_check "external_connector_health_failure" "PASS" "github origin and redis queue connector healthy"
else
  record_check "external_connector_health_failure" "FAIL" "connector failures detected: ${connector_failures}"
fi

{
  echo
  echo "## Summary"
  echo "- pass: ${PASS}"
  echo "- fail: ${FAIL}"
} >> "$OUT"

rm -f "$TMP"
echo "governance_audit_report=$OUT"
