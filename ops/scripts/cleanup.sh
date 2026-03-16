#!/usr/bin/env bash
# ops/scripts/cleanup.sh
# Rule: server should not retain rebuildable or already-offloaded data.
# Run: bash ops/scripts/cleanup.sh
# Cron source: ops/cron/stellcodex-cleanup.cron
set -euo pipefail

WORKSPACE="${WORKSPACE:-/root/workspace}"
DRIVE_ROOT="${DRIVE_ROOT:-gdrive:stellcodex-genois}"
KEEP_RUNS="${KEEP_RUNS:-2}"
REPORT_RETENTION_DAYS="${REPORT_RETENTION_DAYS:-7}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TMP_RETENTION_DAYS="${TMP_RETENTION_DAYS:-1}"
LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-7}"
GIT_TRACKED_AUDIT_LIMIT="${GIT_TRACKED_AUDIT_LIMIT:-5}"

TS="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_PREFIX="[cleanup ${TS}]"

log() {
  echo "${LOG_PREFIX} $*"
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

audit_git_tracked_files() {
  [ -d "${WORKSPACE}/.git" ] || return 0
  has_cmd stat || return 0
  log "GitHub tracked file audit"
  git -C "${WORKSPACE}" ls-files -z \
    | while IFS= read -r -d '' rel; do
        [ -e "${WORKSPACE}/${rel}" ] || continue
        stat -c '%s %n' "${WORKSPACE}/${rel}"
      done \
    | sort -nr \
    | head -n "${GIT_TRACKED_AUDIT_LIMIT}" \
    | awk -v p="${LOG_PREFIX}" '{printf "%s git tracked %s bytes %s\n", p, $1, $2}'
}

drive_ready() {
  has_cmd rclone && rclone lsf "${DRIVE_ROOT}" >/dev/null 2>&1
}

sync_dir_to_drive() {
  local src="$1"
  local dest="$2"
  if ! drive_ready; then
    return 0
  fi
  if [ ! -d "$src" ]; then
    return 0
  fi
  if [ -z "$(find "$src" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    return 0
  fi
  log "Drive sync: ${src} -> ${DRIVE_ROOT}/${dest}"
  rclone sync "${src}/" "${DRIVE_ROOT}/${dest}/" --create-empty-src-dirs >/dev/null
}

keep_latest_dirs() {
  local root="$1"
  local keep="$2"
  [ -d "$root" ] || return 0
  mapfile -t dirs < <(find "$root" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | awk '{print $2}')
  local count="${#dirs[@]}"
  if [ "$count" -le "$keep" ]; then
    return 0
  fi
  log "Pruning ${root}: keeping newest ${keep}, removing $((count - keep))"
  for dir in "${dirs[@]:keep}"; do
    rm -rf "$dir"
  done
}

prune_older_than() {
  local target="$1"
  local age_days="$2"
  [ -d "$target" ] || return 0
  find "$target" -mindepth 1 -mtime +"${age_days}" -exec rm -rf {} + 2>/dev/null || true
}

log "Starting"

if drive_ready; then
  log "Google Drive remote ready: ${DRIVE_ROOT}"
else
  log "WARNING: Google Drive remote not ready; cleanup will skip offload"
fi

if [ -d "${WORKSPACE}/.git" ]; then
  log "GitHub remote check"
  git -C "${WORKSPACE}" remote -v | sed "s/^/${LOG_PREFIX} git /" || true
  git -C "${WORKSPACE}" count-objects -vH | sed "s/^/${LOG_PREFIX} git /" || true
  audit_git_tracked_files || true
fi

# 1. Offload persistent server artifacts before local pruning.
sync_dir_to_drive "${WORKSPACE}/_backups" "server-artifacts/_backups"
sync_dir_to_drive "${WORKSPACE}/backups" "server-artifacts/backups"
sync_dir_to_drive "${WORKSPACE}/_reports" "server-artifacts/_reports"
sync_dir_to_drive "${WORKSPACE}/ops/orchestra/state" "state"

# 2. CPU-only or rebuildable local directories.
if [ -d "${WORKSPACE}/AI/.venv" ]; then
  log "Removing AI/.venv"
  rm -rf "${WORKSPACE}/AI/.venv"
fi

for dir in \
  "${WORKSPACE}/frontend/node_modules" \
  "${WORKSPACE}/frontend/.next" \
  "/var/www/stellcodex/frontend/node_modules" \
  "/var/www/stellcodex/frontend/.next"
do
  if [ -d "$dir" ]; then
    log "Removing rebuildable directory: ${dir}"
    rm -rf "$dir"
  fi
done

# 3. Keep only latest runtime runs.
keep_latest_dirs "${WORKSPACE}/_runs" "${KEEP_RUNS}"

# 4. Python and frontend caches.
find "${WORKSPACE}" -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" \) \
  \( -not -path "*/.git/*" \) -exec rm -rf {} + 2>/dev/null || true
find "${WORKSPACE}" -type f \( -name "*.pyc" -o -name "*.pyo" \) \
  \( -not -path "*/.git/*" \) -delete 2>/dev/null || true

# 5. Temporary build and backup artifacts.
rm -rf \
  "${WORKSPACE}/_stage_patch_backend" \
  "${WORKSPACE}/_stage_patch_frontend" \
  "${WORKSPACE}/_tmp_build_id.txt" \
  /tmp/stellcodex-backup-* \
  2>/dev/null || true

# 6. Log and tmp retention.
find /tmp -maxdepth 1 -type f -mtime +"${TMP_RETENTION_DAYS}" -delete 2>/dev/null || true
find "${WORKSPACE}" -type f -name "*.log" -mtime +"${LOG_RETENTION_DAYS}" -delete 2>/dev/null || true
find /root/.npm/_logs -type f -mtime +"${LOG_RETENTION_DAYS}" -delete 2>/dev/null || true

# 7. Backup and report pruning after offload.
prune_older_than "${WORKSPACE}/_reports" "${REPORT_RETENTION_DAYS}"
prune_older_than "${WORKSPACE}/_backups" "${BACKUP_RETENTION_DAYS}"
prune_older_than "${WORKSPACE}/backups" "${BACKUP_RETENTION_DAYS}"

# 8. Model temp fragments.
find "${WORKSPACE}/_models" -type f -name "*.bin.tmp" -delete 2>/dev/null || true

# 9. Docker reclaim.
if has_cmd docker; then
  log "Pruning dangling Docker objects"
  docker image prune -f 2>/dev/null || true
  docker builder prune -f 2>/dev/null || true
fi

# 10. Git maintenance.
if [ -d "${WORKSPACE}/.git" ]; then
  git -C "${WORKSPACE}" gc --auto >/dev/null 2>&1 || true
fi

log "Completed"
df -h / | tail -1 | awk -v p="${LOG_PREFIX}" '{print p " Disk: "$5" used, "$4" free"}'
