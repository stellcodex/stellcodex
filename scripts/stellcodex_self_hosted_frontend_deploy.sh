#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/root/workspace"
SOURCE_FRONTEND="${STELLCODEX_FRONTEND_SOURCE:-/tmp/stell-main/frontend}"
LIVE_FRONTEND="/var/www/stellcodex/frontend"
LIVE_BACKUP_ROOT="/var/www/stellcodex/_backups"
NGINX_SITE="/etc/nginx/sites-enabled/stellcodex"
PM2_APP="stellcodex-next"
HOST_NAME="stellcodex.com"
HOST_RESOLVE="${HOST_NAME}:443:127.0.0.1"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${ROOT_DIR}/evidence/self_hosted_frontend_deploy_${TIMESTAMP}"
REPORT_PATH="${EVIDENCE_DIR}/report.md"

source "${ROOT_DIR}/scripts/stellcodex_lock.sh"

if ! stellcodex_acquire_lock "self_hosted_frontend_deploy" 1; then
  echo "SELF_HOSTED_FRONTEND_BUSY" >&2
  exit 75
fi

mkdir -p "${EVIDENCE_DIR}"

if [ ! -d "${SOURCE_FRONTEND}" ]; then
  echo "Missing source frontend: ${SOURCE_FRONTEND}" >&2
  exit 2
fi

if [ ! -d "${SOURCE_FRONTEND}/src" ]; then
  echo "Missing source tree: ${SOURCE_FRONTEND}/src" >&2
  exit 2
fi

if [ ! -f "${SOURCE_FRONTEND}/middleware.ts" ]; then
  echo "Missing source middleware: ${SOURCE_FRONTEND}/middleware.ts" >&2
  exit 2
fi

if [ ! -d "${LIVE_FRONTEND}" ]; then
  echo "Missing live frontend root: ${LIVE_FRONTEND}" >&2
  exit 2
fi

if ! grep -q "127.0.0.1:3010" "${NGINX_SITE}"; then
  echo "Nginx site does not point to 127.0.0.1:3010: ${NGINX_SITE}" >&2
  exit 3
fi

SOURCE_REPO="$(cd "${SOURCE_FRONTEND}/.." && pwd)"
SOURCE_GIT_DIR="$(git -C "${SOURCE_REPO}" rev-parse --git-dir)"
SOURCE_GIT_WORK_TREE="$(git -C "${SOURCE_REPO}" rev-parse --show-toplevel)"
SOURCE_HEAD="$(git -C "${SOURCE_REPO}" rev-parse HEAD)"
SOURCE_BRANCH="$(git -C "${SOURCE_REPO}" branch --show-current)"

BACKUP_DIR="${LIVE_BACKUP_ROOT}/frontend_source_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

ROLLBACK_SRC=""
ROLLBACK_MIDDLEWARE=""

rollback() {
  set +e
  if [ -n "${ROLLBACK_SRC}" ] && [ -d "${ROLLBACK_SRC}" ]; then
    if [ -d "${LIVE_FRONTEND}/src" ]; then
      mv "${LIVE_FRONTEND}/src" "${BACKUP_DIR}/failed_src_${TIMESTAMP}" 2>/dev/null || true
    fi
    mv "${ROLLBACK_SRC}" "${LIVE_FRONTEND}/src" 2>/dev/null || true
  fi
  if [ -n "${ROLLBACK_MIDDLEWARE}" ] && [ -f "${ROLLBACK_MIDDLEWARE}" ]; then
    if [ -f "${LIVE_FRONTEND}/middleware.ts" ]; then
      mv "${LIVE_FRONTEND}/middleware.ts" "${BACKUP_DIR}/failed_middleware_${TIMESTAMP}.ts" 2>/dev/null || true
    fi
    mv "${ROLLBACK_MIDDLEWARE}" "${LIVE_FRONTEND}/middleware.ts" 2>/dev/null || true
  fi
}

trap rollback ERR

if [ -d "${LIVE_FRONTEND}/src" ]; then
  mv "${LIVE_FRONTEND}/src" "${BACKUP_DIR}/src"
  ROLLBACK_SRC="${BACKUP_DIR}/src"
fi

if [ -f "${LIVE_FRONTEND}/middleware.ts" ]; then
  mv "${LIVE_FRONTEND}/middleware.ts" "${BACKUP_DIR}/middleware.ts"
  ROLLBACK_MIDDLEWARE="${BACKUP_DIR}/middleware.ts"
fi

cp -a "${SOURCE_FRONTEND}/src" "${LIVE_FRONTEND}/src"
cp -a "${SOURCE_FRONTEND}/middleware.ts" "${LIVE_FRONTEND}/middleware.ts"

(
  cd "${LIVE_FRONTEND}"
  GIT_DIR="${SOURCE_GIT_DIR}" GIT_WORK_TREE="${SOURCE_GIT_WORK_TREE}" npm run build \
    > "${EVIDENCE_DIR}/npm_build.stdout.log" 2> "${EVIDENCE_DIR}/npm_build.stderr.log"
)

pm2 restart "${PM2_APP}" > "${EVIDENCE_DIR}/pm2_restart.log" 2>&1
nginx -t > "${EVIDENCE_DIR}/nginx_test.log" 2>&1
systemctl reload nginx

ready=0
for _ in $(seq 1 30); do
  if curl -sSI "http://127.0.0.1:3010/" > "${EVIDENCE_DIR}/upstream_ready.headers.txt"; then
    ready=1
    break
  fi
  sleep 2
done

if [ "${ready}" -ne 1 ]; then
  echo "Frontend upstream did not become ready on 127.0.0.1:3010" >&2
  exit 4
fi

for path in / /files /projects /shares /admin/health /login /register /reset-password; do
  slug="$(printf '%s' "${path}" | sed 's#^/$#root#; s#[^A-Za-z0-9]#_#g')"
  curl -k -sSI --resolve "${HOST_RESOLVE}" "https://${HOST_NAME}${path}" \
    > "${EVIDENCE_DIR}/route_${slug}.headers.txt"
done

trap - ERR

cat > "${REPORT_PATH}" <<EOF
# Self-Hosted Frontend Deploy

- Timestamp (UTC): \`${TIMESTAMP}\`
- Source frontend: \`${SOURCE_FRONTEND}\`
- Source repo: \`${SOURCE_REPO}\`
- Source branch: \`${SOURCE_BRANCH}\`
- Source HEAD: \`${SOURCE_HEAD}\`
- Live frontend: \`${LIVE_FRONTEND}\`
- Backup dir: \`${BACKUP_DIR}\`
- PM2 app: \`${PM2_APP}\`
- Nginx site: \`${NGINX_SITE}\`

## Route Proof

- \`/\` -> see \`route_root.headers.txt\`
- \`/files\` -> see \`route__files.headers.txt\`
- \`/projects\` -> see \`route__projects.headers.txt\`
- \`/shares\` -> see \`route__shares.headers.txt\`
- \`/admin/health\` -> see \`route__admin_health.headers.txt\`
- \`/login\` -> see \`route__login.headers.txt\`
- \`/register\` -> see \`route__register.headers.txt\`
- \`/reset-password\` -> see \`route__reset_password.headers.txt\`

## Notes

- This deploy path updates the server-hosted frontend directly and does not wait for Vercel.
- Final public traffic cutover still requires Cloudflare/DNS account access if the public edge is not already pointed at this server.
EOF

printf '%s\n' "${REPORT_PATH}"
