#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace"
source "${ROOT}/scripts/stellcodex_lock.sh"
REMOTE_BASE="${REMOTE_BASE:-gdrive:stellcodex}"
REPORT_DIR="${ROOT}/_jobs/reports"
EVIDENCE_ROOT="${ROOT}/evidence"
STATE_FILE="${REPORT_DIR}/stellcodex_backup_guard_state.env"
SUMMARY_JSON="${REPORT_DIR}/stellcodex_backup_guard_latest.json"
SUMMARY_MD="${REPORT_DIR}/stellcodex_backup_guard_latest.md"
FULL_BACKUP_INTERVAL_SECONDS="${FULL_BACKUP_INTERVAL_SECONDS:-86400}"
LOCK_WAIT_SECONDS="${STELLCODEX_BACKUP_LOCK_WAIT_SECONDS:-0}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${EVIDENCE_ROOT}/stateless_backup_${TS}"

mkdir -p "${REPORT_DIR}" "${EVIDENCE_ROOT}" "${RUN_DIR}"

if ! stellcodex_acquire_lock "heavy_ops" "${LOCK_WAIT_SECONDS}"; then
  log() {
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
  }
  log "backup guard skipped: heavy_ops lock busy"
  exit 0
fi

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is required" >&2
  exit 1
fi

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

run_sync() {
  local src="$1"
  local dst="$2"
  if [[ ! -d "${src}" ]]; then
    return 0
  fi
  rclone mkdir "${dst}" >/dev/null
  rclone sync "${src}" "${dst}" --checksum --create-empty-src-dirs
}

stage_runtime_state() {
  local src_root="/tmp/stellcodex_output"
  local dst_root="${RUN_DIR}/runtime_state_snapshot"
  mkdir -p "${dst_root}"
  for name in REPORT.md test_results.json orchestrator.log orchestrator_state.json backup_status.json limits.log limits_state.json; do
    if [[ -f "${src_root}/${name}" ]]; then
      cp "${src_root}/${name}" "${dst_root}/${name}"
    fi
  done
}

upload_if_present() {
  local src="$1"
  local dst="$2"
  local latest_name="$3"
  local summary_path="$4"
  if [[ -f "${src}" ]]; then
    "${ROOT}/scripts/drive_dedup_upload.sh" "${src}" "${dst}" "${latest_name}" >"${summary_path}"
  fi
}

LAST_FULL_BACKUP_EPOCH=0
if [[ -f "${STATE_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${STATE_FILE}"
fi

NOW_EPOCH="$(date -u +%s)"
NEED_FULL_BACKUP=0
if (( NOW_EPOCH - LAST_FULL_BACKUP_EPOCH >= FULL_BACKUP_INTERVAL_SECONDS )); then
  NEED_FULL_BACKUP=1
fi

TRUTH_LOG_PATH=""
if TRUTH_LOG_PATH="$("${ROOT}/scripts/sacred_storage_sync_truth.sh" "${REMOTE_BASE}" 2>/dev/null)"; then
  log "truth sync ok: ${TRUTH_LOG_PATH}"
else
  log "truth sync failed"
  TRUTH_LOG_PATH=""
fi

stage_runtime_state
run_sync "${RUN_DIR}/runtime_state_snapshot" "${REMOTE_BASE}/02_backups/runtime/stellcodex_output_state/current"
run_sync "${ROOT}/_jobs/logs" "${REMOTE_BASE}/02_backups/runtime/jobs_logs/current"
run_sync "${ROOT}/_jobs/output" "${REMOTE_BASE}/02_backups/runtime/jobs_output/current"
run_sync "${ROOT}/_jobs/reports" "${REMOTE_BASE}/12_reports/runtime/current"

upload_if_present \
  "${ROOT}/_jobs/reports/STELLCODEX_SYSTEM_STATE_REPORT.md" \
  "${REMOTE_BASE}/12_reports/system_state" \
  "STELLCODEX_SYSTEM_STATE_REPORT.md" \
  "${RUN_DIR}/report_md_upload.json"

upload_if_present \
  "${ROOT}/_jobs/reports/STELLCODEX_SYSTEM_STATE_REPORT.json" \
  "${REMOTE_BASE}/12_reports/system_state" \
  "STELLCODEX_SYSTEM_STATE_REPORT.json" \
  "${RUN_DIR}/report_json_upload.json"

FULL_BACKUP_STATUS="skipped_recent_full_backup"
DB_DUMP_PATH=""
DB_SHA_PATH=""
STORAGE_ARCHIVE_PATH=""

if (( NEED_FULL_BACKUP == 1 )); then
  FULL_EVIDENCE_DIR="${RUN_DIR}/full"
  mkdir -p "${FULL_EVIDENCE_DIR}"

  EVIDENCE_DIR="${FULL_EVIDENCE_DIR}" "${ROOT}/scripts/backup_db.sh"
  EVIDENCE_DIR="${FULL_EVIDENCE_DIR}" "${ROOT}/scripts/backup_storage.sh"

  DB_DUMP_PATH="$(cat "${FULL_EVIDENCE_DIR}/latest_backup_path.txt" 2>/dev/null || true)"
  DB_SHA_PATH="$(cat "${FULL_EVIDENCE_DIR}/latest_backup_sha_path.txt" 2>/dev/null || true)"
  STORAGE_DIR="$(cat "${FULL_EVIDENCE_DIR}/latest_storage_backup_dir.txt" 2>/dev/null || true)"

  if [[ -n "${STORAGE_DIR}" && -d "${STORAGE_DIR}" ]]; then
    STORAGE_ARCHIVE_PATH="${RUN_DIR}/$(basename "${STORAGE_DIR}").tar.gz"
    tar -C "$(dirname "${STORAGE_DIR}")" -czf "${STORAGE_ARCHIVE_PATH}" "$(basename "${STORAGE_DIR}")"
  fi

  if [[ -n "${DB_DUMP_PATH}" && -f "${DB_DUMP_PATH}" ]]; then
    "${ROOT}/scripts/drive_dedup_upload.sh" "${DB_DUMP_PATH}" "${REMOTE_BASE}/02_backups/full/db" "$(basename "${DB_DUMP_PATH}")" >"${RUN_DIR}/db_dump_upload.json"
    rm -f "${DB_DUMP_PATH}"
  fi

  if [[ -n "${DB_SHA_PATH}" && -f "${DB_SHA_PATH}" ]]; then
    "${ROOT}/scripts/drive_dedup_upload.sh" "${DB_SHA_PATH}" "${REMOTE_BASE}/02_backups/full/db" "$(basename "${DB_SHA_PATH}")" >"${RUN_DIR}/db_sha_upload.json"
  fi

  if [[ -n "${STORAGE_ARCHIVE_PATH}" && -f "${STORAGE_ARCHIVE_PATH}" ]]; then
    "${ROOT}/scripts/drive_dedup_upload.sh" "${STORAGE_ARCHIVE_PATH}" "${REMOTE_BASE}/02_backups/full/storage" "$(basename "${STORAGE_ARCHIVE_PATH}")" >"${RUN_DIR}/storage_upload.json"
    rm -f "${STORAGE_ARCHIVE_PATH}"
  fi

  if [[ -n "${STORAGE_DIR}" && -d "${STORAGE_DIR}" ]]; then
    rm -rf "${STORAGE_DIR}"
  fi

  LAST_FULL_BACKUP_EPOCH="${NOW_EPOCH}"
  cat >"${STATE_FILE}" <<EOF
LAST_FULL_BACKUP_EPOCH=${LAST_FULL_BACKUP_EPOCH}
EOF
  FULL_BACKUP_STATUS="completed"
fi

python3 - <<'PY' "${SUMMARY_JSON}" "${SUMMARY_MD}" "${TS}" "${REMOTE_BASE}" "${TRUTH_LOG_PATH}" "${FULL_BACKUP_STATUS}" "${RUN_DIR}" "${LAST_FULL_BACKUP_EPOCH}"
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
generated_at = sys.argv[3]
remote_base = sys.argv[4]
truth_log = sys.argv[5]
full_backup_status = sys.argv[6]
run_dir = sys.argv[7]
last_full_backup_epoch = int(sys.argv[8] or "0")

run_path = Path(run_dir)
uploads = {}
for path in sorted(run_path.glob("*_upload.json")):
    try:
        uploads[path.name] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        uploads[path.name] = {"error": "invalid_json"}

payload = {
    "generated_at": generated_at,
    "remote_base": remote_base,
    "truth_sync_log": truth_log or None,
    "full_backup_status": full_backup_status,
    "last_full_backup_epoch": last_full_backup_epoch,
    "run_dir": run_dir,
        "uploads": uploads,
        "runtime_syncs": {
        "stellcodex_output_state": f"{remote_base}/02_backups/runtime/stellcodex_output_state/current",
        "jobs_logs": f"{remote_base}/02_backups/runtime/jobs_logs/current",
        "jobs_output": f"{remote_base}/02_backups/runtime/jobs_output/current",
        "reports": f"{remote_base}/12_reports/runtime/current",
        "truth": f"{remote_base}/01_truth",
    },
}
summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
lines = [
    "# STELLCODEX Backup Guard",
    "",
    f"- generated_at: {generated_at}",
    f"- remote_base: {remote_base}",
    f"- truth_sync_log: {truth_log or 'none'}",
    f"- full_backup_status: {full_backup_status}",
    f"- last_full_backup_epoch: {last_full_backup_epoch}",
    f"- run_dir: {run_dir}",
    "",
    "## Runtime Syncs",
    f"- {payload['runtime_syncs']['stellcodex_output_state']}",
    f"- {payload['runtime_syncs']['jobs_logs']}",
    f"- {payload['runtime_syncs']['jobs_output']}",
    f"- {payload['runtime_syncs']['reports']}",
    f"- {payload['runtime_syncs']['truth']}",
    "",
    "## Upload Summaries",
]
if uploads:
    for name, item in uploads.items():
        lines.append(f"- {name}: {item.get('archive_status', 'n/a')} sha256={item.get('sha256', 'n/a')}")
else:
    lines.append("- none")
summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "backup guard complete: ${SUMMARY_JSON}"
