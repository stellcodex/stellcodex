#!/usr/bin/env bash
set -euo pipefail

CORE_ROOT="${CORE_ROOT:-/root/workspace/audit/STELL_SYSTEM_CORE}"
OUT_DIR="$CORE_ROOT/10_reports/provider"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
JSON_OUT="$OUT_DIR/provider_credential_status_${STAMP}.json"
MD_OUT="$OUT_DIR/provider_credential_status_${STAMP}.md"

ENV_FILES=(
  "/root/workspace/.secrets/provider_audit.env"
  "/root/workspace/.env"
  "/root/workspace/.env.local"
  "/root/stell/.secrets/provider_audit.env"
  "/root/stell/.env"
  "/root/stell/.env.local"
  "/root/stell/webhook/.env"
  "/root/stell/webhook/.env.local"
)

mkdir -p "$OUT_DIR"

read_from_file_key() {
  local key="$1"
  local f=""
  local line=""
  local val=""
  for f in "${ENV_FILES[@]}"; do
    [ -f "$f" ] || continue
    line="$(sed -n "s/^${key}=.*/&/p" "$f" | tail -n1 || true)"
    [ -n "$line" ] || continue
    val="${line#*=}"
    val="$(printf '%s' "$val" | sed -e 's/^\"//' -e 's/\"$//' -e "s/^'//" -e "s/'$//" -e 's/[[:space:]]*$//')"
    if [ -n "$val" ]; then
      printf 'file:%s' "$f"
      return 0
    fi
  done
  return 1
}

resolve_key_source() {
  local primary="$1"
  local alias="${2:-}"
  local val=""
  if [ -n "${!primary:-}" ]; then
    printf 'env:%s' "$primary"
    return 0
  fi
  if read_from_file_key "$primary" >/dev/null 2>&1; then
    read_from_file_key "$primary"
    return 0
  fi
  if [ -n "$alias" ]; then
    if [ -n "${!alias:-}" ]; then
      printf 'env:%s' "$alias"
      return 0
    fi
    if read_from_file_key "$alias" >/dev/null 2>&1; then
      read_from_file_key "$alias"
      return 0
    fi
  fi
  return 1
}

cf_token_source="$(resolve_key_source "CLOUDFLARE_API_TOKEN" "CF_API_TOKEN" || true)"
cf_account_source="$(resolve_key_source "CLOUDFLARE_ACCOUNT_ID" "CF_ACCOUNT_ID" || true)"
vercel_token_source="$(resolve_key_source "VERCEL_TOKEN" "" || true)"
vercel_team_source="$(resolve_key_source "VERCEL_TEAM_ID" "VERCEL_ORG_ID" || true)"
vercel_project_source="$(resolve_key_source "VERCEL_PROJECT_ID" "" || true)"

cf_token_present=false
cf_account_present=false
vercel_token_present=false
vercel_team_present=false
vercel_project_present=false

[ -n "$cf_token_source" ] && cf_token_present=true
[ -n "$cf_account_source" ] && cf_account_present=true
[ -n "$vercel_token_source" ] && vercel_token_present=true
[ -n "$vercel_team_source" ] && vercel_team_present=true
[ -n "$vercel_project_source" ] && vercel_project_present=true

summary="BLOCKED_MISSING_CREDENTIALS"
if $cf_token_present && $vercel_token_present; then
  if $cf_account_present && ( $vercel_team_present || $vercel_project_present ); then
    summary="READY_HIGH_CONFIDENCE"
  else
    summary="READY_TOKENS_PRESENT_IDS_RECOMMENDED"
  fi
fi

jq -n \
  --arg ts "$NOW_UTC" \
  --arg summary "$summary" \
  --arg cf_token_source "$cf_token_source" \
  --arg cf_account_source "$cf_account_source" \
  --arg vercel_token_source "$vercel_token_source" \
  --arg vercel_team_source "$vercel_team_source" \
  --arg vercel_project_source "$vercel_project_source" \
  --argjson cf_token_present "$cf_token_present" \
  --argjson cf_account_present "$cf_account_present" \
  --argjson vercel_token_present "$vercel_token_present" \
  --argjson vercel_team_present "$vercel_team_present" \
  --argjson vercel_project_present "$vercel_project_present" \
  --argjson env_files "$(printf '%s\n' "${ENV_FILES[@]}" | jq -R . | jq -s .)" \
  '{
    generated_at_utc: $ts,
    summary: $summary,
    checked_env_files: $env_files,
    cloudflare: {
      token_present: $cf_token_present,
      token_source: (if $cf_token_source == "" then null else $cf_token_source end),
      account_id_present: $cf_account_present,
      account_id_source: (if $cf_account_source == "" then null else $cf_account_source end)
    },
    vercel: {
      token_present: $vercel_token_present,
      token_source: (if $vercel_token_source == "" then null else $vercel_token_source end),
      team_or_org_present: $vercel_team_present,
      team_or_org_source: (if $vercel_team_source == "" then null else $vercel_team_source end),
      project_id_present: $vercel_project_present,
      project_id_source: (if $vercel_project_source == "" then null else $vercel_project_source end)
    }
  }' > "$JSON_OUT"

{
  echo "# Provider Credential Status"
  echo
  echo "- Generated (UTC): $NOW_UTC"
  echo "- Summary: $summary"
  echo
  echo "## Cloudflare"
  echo
  echo "- Token present: $cf_token_present"
  echo "- Token source: ${cf_token_source:-none}"
  echo "- Account ID present: $cf_account_present"
  echo "- Account ID source: ${cf_account_source:-none}"
  echo
  echo "## Vercel"
  echo
  echo "- Token present: $vercel_token_present"
  echo "- Token source: ${vercel_token_source:-none}"
  echo "- Team/Org present: $vercel_team_present"
  echo "- Team/Org source: ${vercel_team_source:-none}"
  echo "- Project ID present: $vercel_project_present"
  echo "- Project ID source: ${vercel_project_source:-none}"
  echo
  echo "## Artifacts"
  echo
  echo "- JSON: $JSON_OUT"
  echo "- Markdown: $MD_OUT"
  echo
  echo "## Checked Env Files"
  printf -- "- %s\n" "${ENV_FILES[@]}"
} > "$MD_OUT"

echo "provider_credential_status_json=$JSON_OUT"
echo "provider_credential_status_md=$MD_OUT"
echo "provider_credential_status_summary=$summary"
