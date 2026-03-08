#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

BACKUP_DIR="${EVIDENCE_DIR}/backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="${BACKUP_DIR}/storage_${STAMP}"
mkdir -p "${TARGET_DIR}"

LOG_FILE="${TARGET_DIR}/backup_storage.txt"
MANIFEST_FILE="${TARGET_DIR}/object_manifest.sha256"

{
  echo "[storage-backup] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "policy=object_mirror"
  echo "target_dir=${TARGET_DIR}"
} | tee "${LOG_FILE}"

if command -v rclone >/dev/null 2>&1 && [[ -n "${RCLONE_STORAGE_SOURCE:-}" ]]; then
  echo "mirror_method=rclone" | tee -a "${LOG_FILE}"
  rclone sync "${RCLONE_STORAGE_SOURCE}" "${TARGET_DIR}/objects" --checkers=8 --transfers=8
elif command -v aws >/dev/null 2>&1 && [[ -n "${S3_BUCKET:-}" ]]; then
  echo "mirror_method=aws_s3_sync" | tee -a "${LOG_FILE}"
  EXTRA_ARGS=()
  if [[ -n "${S3_ENDPOINT_URL:-}" ]]; then
    EXTRA_ARGS+=(--endpoint-url "${S3_ENDPOINT_URL}")
  fi
  SCHEME_SEP="://"
  S3_URI_PREFIX="s3${SCHEME_SEP}"
  aws "${EXTRA_ARGS[@]}" s3 sync "${S3_URI_PREFIX}${S3_BUCKET}" "${TARGET_DIR}/objects"
elif compose ps minio >/dev/null 2>&1; then
  echo "mirror_method=minio_local_volume" | tee -a "${LOG_FILE}"
  require_cmd docker
  mkdir -p "${TARGET_DIR}/objects"
  MINIO_CONTAINER_ID="$(compose ps -q minio | head -n 1)"
  if [[ -z "${MINIO_CONTAINER_ID}" ]]; then
    echo "failed to resolve minio container id for local mirror" | tee -a "${LOG_FILE}"
    exit 1
  fi
  docker cp "${MINIO_CONTAINER_ID}:/data/." "${TARGET_DIR}/objects"
else
  echo "No storage mirror backend configured. Set RCLONE_STORAGE_SOURCE or S3_BUCKET." | tee -a "${LOG_FILE}"
  exit 1
fi

if [[ ! -d "${TARGET_DIR}/objects" ]]; then
  echo "storage mirror failed: objects directory missing" | tee -a "${LOG_FILE}"
  exit 1
fi

(
  cd "${TARGET_DIR}/objects"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "${MANIFEST_FILE}"

OBJECT_COUNT="$(find "${TARGET_DIR}/objects" -type f | wc -l | awk '{print $1}')"
{
  echo "object_count=${OBJECT_COUNT}"
  echo "manifest=${MANIFEST_FILE}"
  echo "[storage-backup] completed"
} | tee -a "${LOG_FILE}"

echo "${TARGET_DIR}" > "${EVIDENCE_DIR}/latest_storage_backup_dir.txt"
