#!/usr/bin/env bash
set -euo pipefail

DEST="gdrive:stellcodex/02_backups/stellcodex_output_backups"
SRC_DIR="/root/stellcodex_output/backups"
RCLONE_FLAGS=(
  --drive-chunk-size 64M
  --retries 20
  --low-level-retries 50
  --stats 30s
  --stats-one-line
  --stats-log-level NOTICE
)

mkdir -p /root/workspace/_truth/12_reports
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="/root/workspace/_truth/12_reports/root_backups_migration_${TS}.log"

{
  echo "[root-backups] started ${TS}"
  rclone mkdir "${DEST}"

  shopt -s nullglob
  files=("${SRC_DIR}"/*.zip)
  shopt -u nullglob
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "[noop] no zip files found in ${SRC_DIR}"
  fi

  for f in "${files[@]}"; do
    base="$(basename "${f}")"
    size_before="$(stat -c '%s' "${f}")"
    sleep 3
    size_after="$(stat -c '%s' "${f}")"
    if [[ "${size_before}" != "${size_after}" ]]; then
      echo "[skip-active] ${base} is still growing (${size_before} -> ${size_after})"
      continue
    fi

    echo "[start] ${base}"
    rclone copyto "${f}" "${DEST}/${base}" "${RCLONE_FLAGS[@]}"
    rmd5="$(rclone md5sum "${DEST}/${base}" | awk '{print $1}' | head -n1)"
    lmd5="$(md5sum "${f}" | awk '{print $1}')"
    echo "[md5] ${base} local=${lmd5} remote=${rmd5}"
    if [[ -z "${rmd5}" || "${lmd5}" != "${rmd5}" ]]; then
      echo "[fail] checksum mismatch for ${base}"
      exit 1
    fi
    rm -f "${f}"
    echo "[done] ${base}"
  done

  rmdir "${SRC_DIR}" 2>/dev/null || true
  echo "[root-backups] PASS"
} | tee "${LOG}"
