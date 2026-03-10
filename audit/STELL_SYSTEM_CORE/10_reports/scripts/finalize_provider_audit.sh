#!/usr/bin/env bash
set -euo pipefail

CORE_ROOT="${CORE_ROOT:-/root/workspace/audit/STELL_SYSTEM_CORE}"
MANIFEST="$CORE_ROOT/ACTIVE_PROMPT_MANIFEST.json"
SYNC_DRIVE="${SYNC_DRIVE:-1}"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PROVIDER_DIR="$CORE_ROOT/10_reports/provider"
MONTHLY_DIR="$CORE_ROOT/10_reports/monthly"

if [ ! -f "$MANIFEST" ]; then
  echo "manifest_missing=$MANIFEST"
  exit 1
fi

cred_out="$(
  /root/workspace/audit/scripts/provider_credential_status.sh
)"
monthly_path="$(
  /root/workspace/audit/scripts/monthly_prompt_audit.sh
)"

latest_provider_json="$(sed -n 's/^- Live audit json: //p' "$monthly_path" | tail -n1)"
latest_provider_md="$(sed -n 's/^- Live audit markdown: //p' "$monthly_path" | tail -n1)"
provider_summary="$(sed -n 's/^- Live audit summary: //p' "$monthly_path" | tail -n1)"
monthly_ts="$(sed -n 's/^- Generated (UTC): //p' "$monthly_path" | head -n1)"

cf_status="unknown"
vercel_status="unknown"
if [ -n "$latest_provider_json" ] && [ -f "$latest_provider_json" ]; then
  cf_status="$(jq -r '.cloudflare.live_api_status // "unknown"' "$latest_provider_json")"
  vercel_status="$(jq -r '.vercel.live_api_status // "unknown"' "$latest_provider_json")"
fi

if [ -z "$latest_provider_json" ]; then
  latest_provider_json="$(ls -1t "$CORE_ROOT"/10_reports/provider/provider_live_audit_*.json 2>/dev/null | head -n1 || true)"
fi
if [ -z "$latest_provider_md" ]; then
  latest_provider_md="$(ls -1t "$CORE_ROOT"/10_reports/provider/provider_live_audit_*.md 2>/dev/null | head -n1 || true)"
fi
if [ -z "$provider_summary" ] && [ -n "$latest_provider_json" ] && [ -f "$latest_provider_json" ]; then
  provider_summary="$(jq -r '.summary // "unknown"' "$latest_provider_json")"
fi

latest_cred_json="$(printf '%s\n' "$cred_out" | sed -n 's/^provider_credential_status_json=//p' | tail -n1)"
latest_cred_md="$(printf '%s\n' "$cred_out" | sed -n 's/^provider_credential_status_md=//p' | tail -n1)"
cred_summary="$(printf '%s\n' "$cred_out" | sed -n 's/^provider_credential_status_summary=//p' | tail -n1)"

if [ -z "$latest_cred_json" ]; then
  latest_cred_json="$(ls -1t "$CORE_ROOT"/10_reports/provider/provider_credential_status_*.json 2>/dev/null | head -n1 || true)"
fi
if [ -z "$latest_cred_md" ]; then
  latest_cred_md="$(ls -1t "$CORE_ROOT"/10_reports/provider/provider_credential_status_*.md 2>/dev/null | head -n1 || true)"
fi
if [ -z "$cred_summary" ] && [ -n "$latest_cred_json" ] && [ -f "$latest_cred_json" ]; then
  cred_summary="$(jq -r '.summary // "unknown"' "$latest_cred_json")"
fi

# Stable pointer files for operational visibility.
latest_provider_alias_json="$PROVIDER_DIR/LATEST_PROVIDER_LIVE_AUDIT.json"
latest_provider_alias_md="$PROVIDER_DIR/LATEST_PROVIDER_LIVE_AUDIT.md"
latest_cred_alias_json="$PROVIDER_DIR/LATEST_PROVIDER_CREDENTIAL_STATUS.json"
latest_cred_alias_md="$PROVIDER_DIR/LATEST_PROVIDER_CREDENTIAL_STATUS.md"
latest_monthly_alias_md="$MONTHLY_DIR/LATEST_MONTHLY_AUDIT.md"
provider_status_json="$PROVIDER_DIR/PROVIDER_AUDIT_STATUS.json"

[ -f "$latest_provider_json" ] && cp "$latest_provider_json" "$latest_provider_alias_json"
[ -f "$latest_provider_md" ] && cp "$latest_provider_md" "$latest_provider_alias_md"
[ -f "$latest_cred_json" ] && cp "$latest_cred_json" "$latest_cred_alias_json"
[ -f "$latest_cred_md" ] && cp "$latest_cred_md" "$latest_cred_alias_md"
[ -f "$monthly_path" ] && cp "$monthly_path" "$latest_monthly_alias_md"

jq -n \
  --arg generated_at_utc "$NOW_UTC" \
  --arg monthly_report "$monthly_path" \
  --arg provider_summary "$provider_summary" \
  --arg provider_json "$latest_provider_json" \
  --arg provider_md "$latest_provider_md" \
  --arg cred_summary "$cred_summary" \
  --arg cred_json "$latest_cred_json" \
  --arg cred_md "$latest_cred_md" \
  --arg cf_status "$cf_status" \
  --arg vercel_status "$vercel_status" \
  --arg provider_alias_json "$latest_provider_alias_json" \
  --arg provider_alias_md "$latest_provider_alias_md" \
  --arg cred_alias_json "$latest_cred_alias_json" \
  --arg cred_alias_md "$latest_cred_alias_md" \
  --arg monthly_alias_md "$latest_monthly_alias_md" \
  '{
    generated_at_utc: $generated_at_utc,
    monthly_report: $monthly_report,
    provider_live_audit: {
      summary: $provider_summary,
      latest_json: $provider_json,
      latest_markdown: $provider_md,
      cloudflare_live_status: $cf_status,
      vercel_live_status: $vercel_status,
      latest_alias_json: $provider_alias_json,
      latest_alias_markdown: $provider_alias_md
    },
    provider_credential_status: {
      summary: $cred_summary,
      latest_json: $cred_json,
      latest_markdown: $cred_md,
      latest_alias_json: $cred_alias_json,
      latest_alias_markdown: $cred_alias_md
    },
    latest_monthly_alias_markdown: $monthly_alias_md
  }' > "$provider_status_json"

TMP="$(mktemp)"
jq \
  --arg now "$NOW_UTC" \
  --arg mts "$monthly_ts" \
  --arg pjson "$latest_provider_json" \
  --arg pmd "$latest_provider_md" \
  --arg ps "$provider_summary" \
  --arg cfs "$cf_status" \
  --arg vs "$vercel_status" \
  --arg cred_json "$latest_cred_json" \
  --arg cred_md "$latest_cred_md" \
  --arg cred_summary "$cred_summary" \
  --arg cred_script "/root/workspace/audit/scripts/provider_credential_status.sh" \
  --arg cred_snapshot "$CORE_ROOT/10_reports/scripts/provider_credential_status.sh" \
  --arg scope_guide "$CORE_ROOT/10_reports/provider/PROVIDER_AUDIT_SCOPE_GUIDE.md" \
  --arg pjson_alias "$latest_provider_alias_json" \
  --arg pmd_alias "$latest_provider_alias_md" \
  --arg cjson_alias "$latest_cred_alias_json" \
  --arg cmd_alias "$latest_cred_alias_md" \
  --arg monthly_alias "$latest_monthly_alias_md" \
  --arg monthly_path "$monthly_path" \
  --arg status_json "$provider_status_json" \
  '
  .external_provider_audit.updated_at_utc = $now |
  .external_provider_audit.external_ingress_snapshot.checked_at_utc = $mts |
  .external_provider_audit.provider_live_audit.latest_json = $pjson |
  .external_provider_audit.provider_live_audit.latest_markdown = $pmd |
  .external_provider_audit.provider_live_audit.latest_alias_json = $pjson_alias |
  .external_provider_audit.provider_live_audit.latest_alias_markdown = $pmd_alias |
  .external_provider_audit.provider_live_audit.summary = $ps |
  .external_provider_audit.provider_live_audit.cloudflare_live_status = $cfs |
  .external_provider_audit.provider_live_audit.vercel_live_status = $vs |
  .external_provider_audit.provider_live_audit.scope_guide = $scope_guide |
  .external_provider_audit.provider_credential_status = {
    latest_json: $cred_json,
    latest_markdown: $cred_md,
    latest_alias_json: $cjson_alias,
    latest_alias_markdown: $cmd_alias,
    summary: $cred_summary,
    script_path: $cred_script,
    snapshot_path: $cred_snapshot
  } |
  .external_provider_audit.last_monthly_report = $monthly_path |
  .external_provider_audit.last_monthly_alias_markdown = $monthly_alias |
  .external_provider_audit.provider_status_file = $status_json
  ' "$MANIFEST" > "$TMP"
mv "$TMP" "$MANIFEST"

if [ "$SYNC_DRIVE" = "1" ]; then
  rclone sync "$CORE_ROOT" gdrive:STELL_SYSTEM_CORE --create-empty-src-dirs >/dev/null
fi

echo "finalize_provider_audit_manifest=$MANIFEST"
echo "finalize_provider_audit_monthly=$monthly_path"
echo "finalize_provider_audit_provider_json=$latest_provider_json"
echo "finalize_provider_audit_provider_md=$latest_provider_md"
echo "finalize_provider_audit_summary=$provider_summary"
echo "finalize_provider_audit_credential_json=$latest_cred_json"
echo "finalize_provider_audit_credential_md=$latest_cred_md"
echo "finalize_provider_audit_credential_summary=$cred_summary"
echo "finalize_provider_audit_provider_alias_json=$latest_provider_alias_json"
echo "finalize_provider_audit_provider_alias_md=$latest_provider_alias_md"
echo "finalize_provider_audit_credential_alias_json=$latest_cred_alias_json"
echo "finalize_provider_audit_credential_alias_md=$latest_cred_alias_md"
echo "finalize_provider_audit_monthly_alias_md=$latest_monthly_alias_md"
echo "finalize_provider_audit_status_json=$provider_status_json"
