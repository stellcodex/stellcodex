#!/usr/bin/env bash
set -euo pipefail

CORE_ROOT="${CORE_ROOT:-/root/workspace/audit/STELL_SYSTEM_CORE}"
OUT_DIR="$CORE_ROOT/10_reports/provider"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
JSON_OUT="$OUT_DIR/provider_live_audit_${STAMP}.json"
MD_OUT="$OUT_DIR/provider_live_audit_${STAMP}.md"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$OUT_DIR"

api_get() {
  local url="$1"
  local token="$2"
  local out="$3"
  curl -sS -m 30 -H "Authorization: Bearer ${token}" -H "Content-Type: application/json" -o "$out" -w "%{http_code}" "$url" || true
}

read_key_from_env_files() {
  local key="$1"
  shift
  local value=""
  local file=""
  for file in "$@"; do
    [ -f "$file" ] || continue
    value="$(sed -n "s/^${key}=//p" "$file" | tail -n1 || true)"
    if [ -n "$value" ]; then
      value="${value%\"}"
      value="${value#\"}"
      value="${value%\'}"
      value="${value#\'}"
      printf '%s' "$value"
      return 0
    fi
  done
  return 1
}

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

cf_token="${CLOUDFLARE_API_TOKEN:-${CF_API_TOKEN:-}}"
if [ -z "$cf_token" ]; then
  cf_token="$(read_key_from_env_files "CLOUDFLARE_API_TOKEN" "${ENV_FILES[@]}" || true)"
fi
if [ -z "$cf_token" ]; then
  cf_token="$(read_key_from_env_files "CF_API_TOKEN" "${ENV_FILES[@]}" || true)"
fi

cf_account_id="${CLOUDFLARE_ACCOUNT_ID:-${CF_ACCOUNT_ID:-}}"
if [ -z "$cf_account_id" ]; then
  cf_account_id="$(read_key_from_env_files "CLOUDFLARE_ACCOUNT_ID" "${ENV_FILES[@]}" || true)"
fi
if [ -z "$cf_account_id" ]; then
  cf_account_id="$(read_key_from_env_files "CF_ACCOUNT_ID" "${ENV_FILES[@]}" || true)"
fi

vercel_token="${VERCEL_TOKEN:-}"
if [ -z "$vercel_token" ]; then
  vercel_token="$(read_key_from_env_files "VERCEL_TOKEN" "${ENV_FILES[@]}" || true)"
fi

vercel_team_id="${VERCEL_TEAM_ID:-${VERCEL_ORG_ID:-}}"
if [ -z "$vercel_team_id" ]; then
  vercel_team_id="$(read_key_from_env_files "VERCEL_TEAM_ID" "${ENV_FILES[@]}" || true)"
fi
if [ -z "$vercel_team_id" ]; then
  vercel_team_id="$(read_key_from_env_files "VERCEL_ORG_ID" "${ENV_FILES[@]}" || true)"
fi

vercel_project_id="${VERCEL_PROJECT_ID:-}"
if [ -z "$vercel_project_id" ]; then
  vercel_project_id="$(read_key_from_env_files "VERCEL_PROJECT_ID" "${ENV_FILES[@]}" || true)"
fi

cf_status="blocked_missing_token"
cf_accounts_http="000"
cf_accounts_count=0
cf_zone_http="000"
cf_zone_id=""
cf_dns_http="000"
cf_dns_count=0
cf_routes_http="000"
cf_routes_count=0
cf_workers_http="000"
cf_workers_count=0
cf_account_used=""

if [ -n "$cf_token" ]; then
  cf_status="api_error"

  cf_accounts_http="$(api_get "https://api.cloudflare.com/client/v4/accounts?per_page=50" "$cf_token" "$TMP_DIR/cf_accounts.json")"
  if [ "$cf_accounts_http" = "200" ] && jq -e '.success == true' "$TMP_DIR/cf_accounts.json" >/dev/null 2>&1; then
    cf_accounts_count="$(jq -r '(.result // []) | length' "$TMP_DIR/cf_accounts.json")"
    if [ -z "$cf_account_id" ]; then
      cf_account_id="$(jq -r '(.result // [])[0].id // ""' "$TMP_DIR/cf_accounts.json")"
    fi
  fi

  if [ -n "$cf_account_id" ]; then
    cf_account_used="$cf_account_id"
    cf_workers_http="$(api_get "https://api.cloudflare.com/client/v4/accounts/${cf_account_id}/workers/scripts" "$cf_token" "$TMP_DIR/cf_workers.json")"
    if [ "$cf_workers_http" = "200" ] && jq -e '.success == true' "$TMP_DIR/cf_workers.json" >/dev/null 2>&1; then
      cf_workers_count="$(jq -r '(.result // []) | length' "$TMP_DIR/cf_workers.json")"
    fi
  fi

  cf_zone_http="$(api_get "https://api.cloudflare.com/client/v4/zones?name=stellcodex.com&status=active" "$cf_token" "$TMP_DIR/cf_zones.json")"
  if [ "$cf_zone_http" = "200" ] && jq -e '.success == true' "$TMP_DIR/cf_zones.json" >/dev/null 2>&1; then
    cf_zone_id="$(jq -r '(.result // [])[0].id // ""' "$TMP_DIR/cf_zones.json")"
  fi

  if [ -n "$cf_zone_id" ]; then
    cf_dns_http="$(api_get "https://api.cloudflare.com/client/v4/zones/${cf_zone_id}/dns_records?per_page=5000" "$cf_token" "$TMP_DIR/cf_dns_records.json")"
    if [ "$cf_dns_http" = "200" ] && jq -e '.success == true' "$TMP_DIR/cf_dns_records.json" >/dev/null 2>&1; then
      cf_dns_count="$(jq -r '(.result // []) | length' "$TMP_DIR/cf_dns_records.json")"
    fi

    cf_routes_http="$(api_get "https://api.cloudflare.com/client/v4/zones/${cf_zone_id}/workers/routes?per_page=5000" "$cf_token" "$TMP_DIR/cf_worker_routes.json")"
    if [ "$cf_routes_http" = "200" ] && jq -e '.success == true' "$TMP_DIR/cf_worker_routes.json" >/dev/null 2>&1; then
      cf_routes_count="$(jq -r '(.result // []) | length' "$TMP_DIR/cf_worker_routes.json")"
    fi
  fi

  if [ "$cf_accounts_http" = "200" ] || [ "$cf_zone_http" = "200" ] || [ "$cf_workers_http" = "200" ]; then
    cf_status="ok"
  fi
fi

vercel_status="blocked_missing_token"
vercel_projects_http="000"
vercel_projects_count=0
vercel_deployments_http="000"
vercel_deployments_count=0
vercel_env_http="000"
vercel_env_count=0
vercel_project_used=""

if [ -n "$vercel_token" ]; then
  vercel_status="api_error"
  vercel_qs=""
  if [ -n "$vercel_team_id" ]; then
    vercel_qs="?teamId=${vercel_team_id}"
  fi
  if [ -z "$vercel_qs" ]; then
    vercel_qs="?limit=100"
  else
    vercel_qs="${vercel_qs}&limit=100"
  fi

  vercel_projects_http="$(api_get "https://api.vercel.com/v9/projects${vercel_qs}" "$vercel_token" "$TMP_DIR/vercel_projects.json")"
  if [ "$vercel_projects_http" = "200" ]; then
    vercel_projects_count="$(jq -r '(.projects // []) | length' "$TMP_DIR/vercel_projects.json")"
    if [ -z "$vercel_project_id" ]; then
      vercel_project_id="$(jq -r '(.projects // [] | map(select((.name // \"\") | test(\"stell\";\"i\")))[0].id) // \"\"' "$TMP_DIR/vercel_projects.json")"
    fi
  fi

  vercel_deploy_qs=""
  if [ -n "$vercel_team_id" ]; then
    vercel_deploy_qs="?teamId=${vercel_team_id}&limit=20"
  else
    vercel_deploy_qs="?limit=20"
  fi
  vercel_deployments_http="$(api_get "https://api.vercel.com/v6/deployments${vercel_deploy_qs}" "$vercel_token" "$TMP_DIR/vercel_deployments.json")"
  if [ "$vercel_deployments_http" = "200" ]; then
    vercel_deployments_count="$(jq -r '(.deployments // []) | length' "$TMP_DIR/vercel_deployments.json")"
  fi

  if [ -n "$vercel_project_id" ]; then
    vercel_project_used="$vercel_project_id"
    vercel_env_qs="?decrypt=false"
    if [ -n "$vercel_team_id" ]; then
      vercel_env_qs="${vercel_env_qs}&teamId=${vercel_team_id}"
    fi
    vercel_env_http="$(api_get "https://api.vercel.com/v9/projects/${vercel_project_id}/env${vercel_env_qs}" "$vercel_token" "$TMP_DIR/vercel_env.json")"
    if [ "$vercel_env_http" = "200" ]; then
      vercel_env_count="$(jq -r '(.envs // []) | length' "$TMP_DIR/vercel_env.json")"
    fi
  fi

  if [ "$vercel_projects_http" = "200" ] || [ "$vercel_deployments_http" = "200" ] || [ "$vercel_env_http" = "200" ]; then
    vercel_status="ok"
  fi
fi

summary="PASS"
if [[ "$cf_status" == blocked_* ]] && [[ "$vercel_status" == blocked_* ]]; then
  summary="BLOCKED_MISSING_CREDENTIALS"
elif [[ "$cf_status" == ok ]] && [[ "$vercel_status" == ok ]]; then
  summary="PASS"
elif [[ "$cf_status" == ok ]] || [[ "$vercel_status" == ok ]]; then
  summary="PARTIAL"
else
  summary="WARN"
fi

jq -n \
  --arg generated_at_utc "$NOW_UTC" \
  --arg summary "$summary" \
  --arg cf_status "$cf_status" \
  --arg cf_accounts_http "$cf_accounts_http" \
  --argjson cf_accounts_count "$cf_accounts_count" \
  --arg cf_account_id_present "$( [ -n "$cf_account_id" ] && echo true || echo false )" \
  --arg cf_account_used "$cf_account_used" \
  --arg cf_zone_http "$cf_zone_http" \
  --arg cf_zone_id "$cf_zone_id" \
  --arg cf_dns_http "$cf_dns_http" \
  --argjson cf_dns_count "$cf_dns_count" \
  --arg cf_routes_http "$cf_routes_http" \
  --argjson cf_routes_count "$cf_routes_count" \
  --arg cf_workers_http "$cf_workers_http" \
  --argjson cf_workers_count "$cf_workers_count" \
  --arg vercel_status "$vercel_status" \
  --arg vercel_projects_http "$vercel_projects_http" \
  --argjson vercel_projects_count "$vercel_projects_count" \
  --arg vercel_deployments_http "$vercel_deployments_http" \
  --argjson vercel_deployments_count "$vercel_deployments_count" \
  --arg vercel_project_id_present "$( [ -n "$vercel_project_id" ] && echo true || echo false )" \
  --arg vercel_project_used "$vercel_project_used" \
  --arg vercel_env_http "$vercel_env_http" \
  --argjson vercel_env_count "$vercel_env_count" \
  '{
    generated_at_utc: $generated_at_utc,
    summary: $summary,
    cloudflare: {
      live_api_status: $cf_status,
      account_id_present: ($cf_account_id_present == "true"),
      account_used: (if $cf_account_used == "" then null else $cf_account_used end),
      accounts_http: $cf_accounts_http,
      accounts_count: $cf_accounts_count,
      zone_http: $cf_zone_http,
      zone_id: (if $cf_zone_id == "" then null else $cf_zone_id end),
      dns_records_http: $cf_dns_http,
      dns_records_count: $cf_dns_count,
      worker_routes_http: $cf_routes_http,
      worker_routes_count: $cf_routes_count,
      workers_scripts_http: $cf_workers_http,
      workers_scripts_count: $cf_workers_count
    },
    vercel: {
      live_api_status: $vercel_status,
      project_id_present: ($vercel_project_id_present == "true"),
      project_used: (if $vercel_project_used == "" then null else $vercel_project_used end),
      projects_http: $vercel_projects_http,
      projects_count: $vercel_projects_count,
      deployments_http: $vercel_deployments_http,
      deployments_count: $vercel_deployments_count,
      env_http: $vercel_env_http,
      env_count: $vercel_env_count
    }
  }' > "$JSON_OUT"

{
  echo "# Provider Live Audit"
  echo
  echo "- Generated (UTC): $NOW_UTC"
  echo "- Summary: $summary"
  echo
  echo "## Cloudflare"
  echo
  echo "- Status: $cf_status"
  echo "- Account ID present: $( [ -n "$cf_account_id" ] && echo yes || echo no )"
  echo "- Accounts API: HTTP $cf_accounts_http (count=$cf_accounts_count)"
  echo "- Zone lookup API: HTTP $cf_zone_http (zone_id=${cf_zone_id:-none})"
  echo "- DNS records API: HTTP $cf_dns_http (count=$cf_dns_count)"
  echo "- Worker routes API: HTTP $cf_routes_http (count=$cf_routes_count)"
  echo "- Worker scripts API: HTTP $cf_workers_http (count=$cf_workers_count)"
  echo
  echo "## Vercel"
  echo
  echo "- Status: $vercel_status"
  echo "- Team/Org ID present: $( [ -n "$vercel_team_id" ] && echo yes || echo no )"
  echo "- Project ID present: $( [ -n "$vercel_project_id" ] && echo yes || echo no )"
  echo "- Projects API: HTTP $vercel_projects_http (count=$vercel_projects_count)"
  echo "- Deployments API: HTTP $vercel_deployments_http (count=$vercel_deployments_count)"
  echo "- Project env API: HTTP $vercel_env_http (count=$vercel_env_count)"
  echo
  echo "## Artifacts"
  echo
  echo "- JSON: $JSON_OUT"
  echo "- Markdown: $MD_OUT"
} > "$MD_OUT"

echo "provider_live_audit_json=$JSON_OUT"
echo "provider_live_audit_md=$MD_OUT"
echo "cloudflare_live_status=$cf_status"
echo "vercel_live_status=$vercel_status"
echo "provider_live_audit_summary=$summary"
