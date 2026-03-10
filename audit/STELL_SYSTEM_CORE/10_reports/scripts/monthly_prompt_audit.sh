#!/usr/bin/env bash
set -euo pipefail

CORE_ROOT="/root/workspace/audit/STELL_SYSTEM_CORE"
REPORT_ROOT="$CORE_ROOT/10_reports/monthly"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT="$REPORT_ROOT/monthly_audit_${STAMP}.md"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$REPORT_ROOT"

INV_JSON="$CORE_ROOT/10_reports/MASTER_PROMPT_INVENTORY.json"
DUP_JSON="$CORE_ROOT/10_reports/PROMPT_DUPLICATES.json"
CON_JSON="$CORE_ROOT/10_reports/PROMPT_CONFLICTS.json"
MANIFEST_JSON="$CORE_ROOT/ACTIVE_PROMPT_MANIFEST.json"

inventory_rows="$(jq 'length' "$INV_JSON")"
active_rows="$(jq '[.[] | select(.status=="active")] | length' "$INV_JSON")"
legacy_rows="$(jq '[.[] | select(.status=="legacy/deprecated")] | length' "$INV_JSON")"
duplicate_groups="$(jq 'length' "$DUP_JSON")"
conflict_groups="$(jq 'length' "$CON_JSON")"
manifest_rows="$(jq -r '.stats.inventory_rows // "missing"' "$MANIFEST_JSON")"

drift_status="FAIL"
if python3 /root/stell/scripts/prompt_drift_guard.py >"$TMP_DIR/drift.txt" 2>&1; then
  drift_status="PASS"
fi

webhook_pid="$(pm2 pid stell-webhook 2>/dev/null || true)"
webhook_env_status="FAIL"
webhook_health_status="FAIL"
if [[ "$webhook_pid" =~ ^[0-9]+$ ]] && [[ -r "/proc/$webhook_pid/environ" ]]; then
  if tr '\0' '\n' <"/proc/$webhook_pid/environ" | rg -q '^STELL_PROMPT_MANIFEST_PATH=' \
    && tr '\0' '\n' <"/proc/$webhook_pid/environ" | rg -q '^STELL_REQUIRE_PROMPT_MANIFEST=1$'; then
    webhook_env_status="PASS"
  fi
fi
if curl -sS -m 10 http://127.0.0.1:4500/stell/health >"$TMP_DIR/webhook_health.json" 2>"$TMP_DIR/webhook_health.err"; then
  if jq -e '.status == "healthy"' "$TMP_DIR/webhook_health.json" >/dev/null 2>&1; then
    webhook_health_status="PASS"
  fi
fi

orchestrator_status="FAIL"
if docker exec orchestra_orchestrator_1 python -c 'import app, profiler; assert app.REQUIRE_EXTERNAL_PROMPTS is True; assert profiler.REQUIRE_EXTERNAL_PROMPTS is True; assert app.ORCHESTRATOR_PROMPTS_PATH.exists(); assert profiler.ORCHESTRATOR_PROMPTS_PATH.exists(); print("ok")' >"$TMP_DIR/orch.txt" 2>&1; then
  orchestrator_status="PASS"
fi

cloudflare_token="absent"
vercel_token="absent"
if env | rg -q '^(CLOUDFLARE_API_TOKEN|CF_API_TOKEN)='; then
  cloudflare_token="present"
fi
if env | rg -q '^VERCEL_TOKEN='; then
  vercel_token="present"
fi

provider_live_status="not_run"
provider_live_summary="unknown"
provider_live_md="(none)"
provider_live_json="(none)"
if [ -x /root/workspace/audit/scripts/provider_live_audit.sh ]; then
  provider_live_status="PASS"
  if provider_out="$(/root/workspace/audit/scripts/provider_live_audit.sh 2>&1)"; then
    printf '%s\n' "$provider_out" > "$TMP_DIR/provider_live_output.txt"
    provider_live_summary="$(printf '%s\n' "$provider_out" | sed -n 's/^provider_live_audit_summary=//p' | tail -n1)"
    provider_live_md="$(printf '%s\n' "$provider_out" | sed -n 's/^provider_live_audit_md=//p' | tail -n1)"
    provider_live_json="$(printf '%s\n' "$provider_out" | sed -n 's/^provider_live_audit_json=//p' | tail -n1)"
  else
    provider_live_status="FAIL"
    printf '%s\n' "$provider_out" > "$TMP_DIR/provider_live_output.txt"
  fi
fi

# External ingress sanity checks (no provider API credentials required).
# Note: workers.dev hostname is account-specific and cannot be validated
# deterministically without provider-side metadata.
declare -a endpoint_specs=(
  "https://stellcodex.com|200,301,302,307,308"
  "https://api.stellcodex.com/api/v1/health|200"
  "https://stell.stellcodex.com/stell/webhook|200,400,401,403,405"
)

external_summary="PASS"
{
  for spec in "${endpoint_specs[@]}"; do
    url="${spec%%|*}"
    expected_codes="${spec#*|}"
    host="$(printf '%s' "$url" | sed -E 's#^https?://([^/]+).*#\1#')"
    resolved="no"
    if getent ahosts "$host" >/dev/null 2>&1; then
      resolved="yes"
    fi
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 12 "$url" 2>/dev/null || true)"
    [ -n "$code" ] || code="000"
    verdict="ok"
    if [ "$resolved" != "yes" ] || [ "$code" = "000" ]; then
      verdict="fail"
      external_summary="FAIL"
    elif ! printf '%s' ",$expected_codes," | rg -q ",$code,"; then
      verdict="warn"
      if [ "$external_summary" = "PASS" ]; then external_summary="WARN"; fi
    fi
    printf -- "- %s | resolve=%s | http=%s | expected=%s | verdict=%s\n" "$url" "$resolved" "$code" "$expected_codes" "$verdict"
  done
  echo "- workers.dev endpoint check: skipped (account-specific host unknown without Cloudflare API metadata)"
} > "$TMP_DIR/external_endpoints.txt"

{
  echo "# STELL Monthly Prompt Audit"
  echo
  echo "- Generated (UTC): $NOW_UTC"
  echo "- Inventory rows: $inventory_rows"
  echo "- Active rows: $active_rows"
  echo "- Legacy rows: $legacy_rows"
  echo "- Duplicate groups: $duplicate_groups"
  echo "- Conflict groups: $conflict_groups"
  echo "- Manifest stats.inventory_rows: $manifest_rows"
  echo
  echo "## Runtime Enforcement Checks"
  echo
  echo "- Prompt drift guard: $drift_status"
  echo "- Webhook env strict mapping: $webhook_env_status"
  echo "- Webhook health endpoint: $webhook_health_status"
  echo "- Orchestrator strict template mode: $orchestrator_status"
  echo
  echo "## Provider Credential Presence"
  echo
  echo "- Cloudflare audit token: $cloudflare_token"
  echo "- Vercel audit token: $vercel_token"
  echo
  echo "## Provider API Live Audit"
  echo
  echo "- Script run status: $provider_live_status"
  echo "- Live audit summary: ${provider_live_summary:-unknown}"
  echo "- Live audit markdown: ${provider_live_md:-'(none)'}"
  echo "- Live audit json: ${provider_live_json:-'(none)'}"
  if [ -f "$TMP_DIR/provider_live_output.txt" ]; then
    echo
    echo '```text'
    cat "$TMP_DIR/provider_live_output.txt"
    echo '```'
  fi
  echo
  echo "## External Endpoint Reachability"
  echo
  echo "- Summary: $external_summary"
  cat "$TMP_DIR/external_endpoints.txt"
  echo
  echo "## Drift Guard Output"
  echo
  echo '```text'
  cat "$TMP_DIR/drift.txt"
  echo '```'
} >"$OUT"

# Keep central folder mirrored on Drive after every monthly audit run.
rclone sync "$CORE_ROOT" gdrive:STELL_SYSTEM_CORE --create-empty-src-dirs >/dev/null

echo "$OUT"
