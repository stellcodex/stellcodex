#!/usr/bin/env bash
set -euo pipefail

REMOTE_BASE="${1:-gdrive:stellcodex}"
ROOT="/root/workspace"
REPORT_DIR="${ROOT}/_truth/12_reports"
mkdir -p "${REPORT_DIR}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="${REPORT_DIR}/drive_migrate_${TS}.log"
TAR_MODE_FOR_LARGE="${TAR_MODE_FOR_LARGE:-1}"

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is required" >&2
  exit 1
fi

migrate_dir() {
  local src="$1"
  local remote_dir="$2"
  local label="$3"

  if [[ ! -e "${src}" ]]; then
    echo "[skip] ${label}: missing ${src}"
    return 0
  fi
  if [[ -d "${src}" && -z "$(find "${src}" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "[skip] ${label}: empty ${src}"
    return 0
  fi

  local base
  base="$(basename "${src}")"
  local dst="${REMOTE_BASE}/${remote_dir}/${base}"

  echo "[detect] ${label}: ${src}"
  rclone mkdir "${REMOTE_BASE}/${remote_dir}"
  echo "[upload] ${label}: ${src} -> ${dst}"
  rclone copy "${src}" "${dst}" --checksum
  echo "[verify] ${label}: ${src} <-> ${dst}"
  rclone check "${src}" "${dst}" --checksum --one-way
  echo "[delete] ${label}: ${src}"
  rm -rf "${src}"
  echo "[pass] ${label}: ${src}"
}

migrate_dir_tar() {
  local src="$1"
  local remote_dir="$2"
  local label="$3"

  if [[ ! -e "${src}" ]]; then
    echo "[skip] ${label}: missing ${src}"
    return 0
  fi
  if [[ -d "${src}" && -z "$(find "${src}" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "[skip] ${label}: empty ${src}"
    return 0
  fi

  local base
  base="$(basename "${src}")"
  local tar_file="/tmp/${base}_${TS}.tar.gz"
  local remote_path="${REMOTE_BASE}/${remote_dir}/tarballs"

  echo "[pack] ${label}: ${src} -> ${tar_file}"
  tar -czf "${tar_file}" -C "$(dirname "${src}")" "${base}"
  local local_md5
  local_md5="$(md5sum "${tar_file}" | awk '{print $1}')"

  rclone mkdir "${remote_path}"
  echo "[upload] ${label}: ${tar_file} -> ${remote_path}"
  rclone copy "${tar_file}" "${remote_path}"

  local remote_md5
  remote_md5="$(rclone md5sum "${remote_path}/$(basename "${tar_file}")" | awk '{print $1}' | head -n1)"
  if [[ -z "${remote_md5}" || "${local_md5}" != "${remote_md5}" ]]; then
    echo "[fail] ${label}: md5 mismatch local=${local_md5} remote=${remote_md5}" >&2
    return 1
  fi

  echo "[delete] ${label}: ${src}"
  rm -rf "${src}" "${tar_file}"
  echo "[pass] ${label}: ${src} (tar+md5)"
}

{
  echo "[migrate] started ${TS}"

  migrate_dir "/root/workspace/_backups" "02_backups" "BACKUP"
  migrate_dir "/root/workspace/_jobs/backups" "02_backups" "BACKUP"
  if [[ "${TAR_MODE_FOR_LARGE}" == "1" ]]; then
    migrate_dir_tar "/root/stellcodex_output/backups" "02_backups" "BACKUP"
    migrate_dir_tar "/var/backups/stellcodex" "02_backups" "BACKUP"
  else
    migrate_dir "/root/stellcodex_output/backups" "02_backups" "BACKUP"
    migrate_dir "/var/backups/stellcodex" "02_backups" "BACKUP"
  fi

  migrate_dir "/root/workspace/evidence" "03_evidence" "EVIDENCE"
  migrate_dir "/root/workspace/audit/output" "03_evidence" "EVIDENCE"

  migrate_dir "/root/workspace/_jobs/logs" "04_reports" "REPORT"
  migrate_dir "/root/workspace/handoff" "04_reports" "REPORT"

  migrate_dir "/root/workspace/_datasets" "05_datasets" "DATASET"
  migrate_dir "/root/workspace/_packages/datasets" "05_datasets" "DATASET"

  migrate_dir "/root/workspace/archive_legacy" "06_archive" "ARCHIVE"
  if [[ "${TAR_MODE_FOR_LARGE}" == "1" ]]; then
    migrate_dir_tar "/tmp/stellcodex_restore_test_1772153962" "06_archive" "ARCHIVE"
    migrate_dir_tar "/tmp/stellcodex_restore_test_1772154433" "06_archive" "ARCHIVE"
  else
    migrate_dir "/tmp/stellcodex_restore_test_1772153962" "06_archive" "ARCHIVE"
    migrate_dir "/tmp/stellcodex_restore_test_1772154433" "06_archive" "ARCHIVE"
  fi

  echo "[migrate] PASS"
} | tee "${LOG_FILE}"

echo "${LOG_FILE}"
