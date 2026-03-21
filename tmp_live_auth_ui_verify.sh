#!/usr/bin/env bash
set -euo pipefail

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ENV_FILE=/var/www/stellcodex/infrastructure/deploy/.env

read_env() {
  local key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | head -n1
}

AUTH_SEED_MEMBER_EMAIL=$(read_env AUTH_SEED_MEMBER_EMAIL)
AUTH_SEED_MEMBER_PASSWORD=$(read_env AUTH_SEED_MEMBER_PASSWORD)
AUTH_SEED_ADMIN_EMAIL=$(read_env AUTH_SEED_ADMIN_EMAIL)
AUTH_SEED_ADMIN_PASSWORD=$(read_env AUTH_SEED_ADMIN_PASSWORD)

BASE=https://stellcodex.com
MEMBER_COOKIE="$TMP/member.cookies"
ADMIN_COOKIE="$TMP/admin.cookies"

cat > "$TMP/demo.stl" <<'EOF'
solid demo
 facet normal 0 0 0
  outer loop
   vertex 0 0 0
   vertex 1 0 0
   vertex 0 1 0
  endloop
 endfacet
endsolid demo
EOF

member_login_code=$(curl -sS -c "$MEMBER_COOKIE" -b "$MEMBER_COOKIE" -o "$TMP/member_login.json" -w "%{http_code}" -H "Content-Type: application/json" -X POST "$BASE/api/v1/auth/login" --data "{\"email\":\"$AUTH_SEED_MEMBER_EMAIL\",\"password\":\"$AUTH_SEED_MEMBER_PASSWORD\"}")
member_role=$(jq -r '.role' "$TMP/member_login.json")
admin_login_code=$(curl -sS -c "$ADMIN_COOKIE" -b "$ADMIN_COOKIE" -o "$TMP/admin_login.json" -w "%{http_code}" -H "Content-Type: application/json" -X POST "$BASE/api/v1/auth/login" --data "{\"email\":\"$AUTH_SEED_ADMIN_EMAIL\",\"password\":\"$AUTH_SEED_ADMIN_PASSWORD\"}")
admin_role=$(jq -r '.role' "$TMP/admin_login.json")

sign_in_html=$(curl -sS "$BASE/sign-in")
sign_in_has_title=0
sign_in_has_settings_word=0
[[ "$sign_in_html" == *"Sign in"* ]] && sign_in_has_title=1
[[ "$sign_in_html" == *">Settings<"* ]] && sign_in_has_settings_word=1 || true

curl -sS -D "$TMP/dash_anon.headers" -o /dev/null "$BASE/dashboard" >/dev/null
dash_anon_status=$(awk 'toupper($1) ~ /^HTTP\// { code=$2 } END { print code }' "$TMP/dash_anon.headers")
dash_anon_location=$(awk 'tolower($1) == "location:" { print $2 }' "$TMP/dash_anon.headers" | tail -n1 | tr -d '\r')

curl -sS -D "$TMP/settings_anon.headers" -o /dev/null "$BASE/settings" >/dev/null
settings_anon_status=$(awk 'toupper($1) ~ /^HTTP\// { code=$2 } END { print code }' "$TMP/settings_anon.headers")
settings_anon_location=$(awk 'tolower($1) == "location:" { print $2 }' "$TMP/settings_anon.headers" | tail -n1 | tr -d '\r')

upload_code=$(curl -sS -b "$MEMBER_COOKIE" -o "$TMP/upload.json" -w "%{http_code}" -F "upload=@$TMP/demo.stl;type=model/stl" "$BASE/api/v1/files/upload")
file_id=$(jq -r '.file_id' "$TMP/upload.json")

status_state=""
for _ in $(seq 1 30); do
  curl -sS -b "$MEMBER_COOKIE" -o "$TMP/status.json" "$BASE/api/v1/files/$file_id/status"
  status_state=$(jq -r '.state // empty' "$TMP/status.json")
  if [[ "$status_state" == "succeeded" || "$status_state" == "failed" ]]; then
    break
  fi
  sleep 2
done

member_dashboard_code=$(curl -sS -b "$MEMBER_COOKIE" -o "$TMP/dashboard.html" -w "%{http_code}" "$BASE/dashboard")
member_settings_code=$(curl -sS -b "$MEMBER_COOKIE" -o "$TMP/settings.html" -w "%{http_code}" "$BASE/settings")
member_viewer_code=$(curl -sS -b "$MEMBER_COOKIE" -o "$TMP/viewer.html" -w "%{http_code}" "$BASE/files/$file_id/viewer")
admin_code=$(curl -sS -b "$ADMIN_COOKIE" -o "$TMP/admin.html" -w "%{http_code}" "$BASE/admin")

curl -sS -D "$TMP/viewer_anon.headers" -o /dev/null "$BASE/files/$file_id/viewer" >/dev/null
viewer_anon_status=$(awk 'toupper($1) ~ /^HTTP\// { code=$2 } END { print code }' "$TMP/viewer_anon.headers")
viewer_anon_location=$(awk 'tolower($1) == "location:" { print $2 }' "$TMP/viewer_anon.headers" | tail -n1 | tr -d '\r')

dashboard_html=$(cat "$TMP/dashboard.html")
shell_has_white=0
shell_has_sidebar_state=0
shell_has_wordmark=0
shell_has_subtitle=0
shell_has_active_nav=0
[[ "$dashboard_html" == *"bg-white"* ]] && shell_has_white=1
[[ "$dashboard_html" == *'data-sidebar-state="expanded"'* ]] && shell_has_sidebar_state=1
[[ "$dashboard_html" == *"STELLCODEX"* ]] && shell_has_wordmark=1
[[ "$dashboard_html" == *"Manufacturing decision workspace"* ]] && shell_has_subtitle=1
[[ "$dashboard_html" == *"bg-[var(--background-subtle)] text-[var(--foreground-strong)]"* ]] && shell_has_active_nav=1

share_create_code=000
public_share_code=000
public_share_page_code=000
if [[ "$status_state" == "succeeded" ]]; then
  share_create_code=$(curl -sS -b "$MEMBER_COOKIE" -o "$TMP/share.json" -w "%{http_code}" -H "Content-Type: application/json" -X POST "$BASE/api/v1/shares" --data "{\"file_id\":\"$file_id\",\"permission\":\"view\",\"expires_in_seconds\":600}")
  share_token=$(jq -r '.token // empty' "$TMP/share.json")
  if [[ -n "$share_token" ]]; then
    public_share_code=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/v1/s/$share_token")
    public_share_page_code=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/s/$share_token")
  fi
fi

google_start_code=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/v1/auth/google/start?next=%2Fdashboard")

printf 'member_login_code=%s\n' "$member_login_code"
printf 'member_role=%s\n' "$member_role"
printf 'admin_login_code=%s\n' "$admin_login_code"
printf 'admin_role=%s\n' "$admin_role"
printf 'sign_in_has_title=%s\n' "$sign_in_has_title"
printf 'sign_in_has_settings_word=%s\n' "$sign_in_has_settings_word"
printf 'dash_anon_status=%s\n' "$dash_anon_status"
printf 'dash_anon_location=%s\n' "$dash_anon_location"
printf 'settings_anon_status=%s\n' "$settings_anon_status"
printf 'settings_anon_location=%s\n' "$settings_anon_location"
printf 'upload_code=%s\n' "$upload_code"
printf 'file_id=%s\n' "$file_id"
printf 'status_state=%s\n' "$status_state"
printf 'member_dashboard_code=%s\n' "$member_dashboard_code"
printf 'member_settings_code=%s\n' "$member_settings_code"
printf 'member_viewer_code=%s\n' "$member_viewer_code"
printf 'viewer_anon_status=%s\n' "$viewer_anon_status"
printf 'viewer_anon_location=%s\n' "$viewer_anon_location"
printf 'admin_code=%s\n' "$admin_code"
printf 'shell_has_white=%s\n' "$shell_has_white"
printf 'shell_has_sidebar_state=%s\n' "$shell_has_sidebar_state"
printf 'shell_has_wordmark=%s\n' "$shell_has_wordmark"
printf 'shell_has_subtitle=%s\n' "$shell_has_subtitle"
printf 'shell_has_active_nav=%s\n' "$shell_has_active_nav"
printf 'share_create_code=%s\n' "$share_create_code"
printf 'public_share_code=%s\n' "$public_share_code"
printf 'public_share_page_code=%s\n' "$public_share_page_code"
printf 'google_start_code=%s\n' "$google_start_code"
