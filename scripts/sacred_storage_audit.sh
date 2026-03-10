#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace"
REPORT_DIR="${ROOT}/_truth/12_reports"
mkdir -p "${REPORT_DIR}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${REPORT_DIR}/disk_audit_${TS}.md"

categorize() {
  local p="$1"
  case "$p" in
    *docker*|*/var/lib/docker*|*/var/lib/postgresql*|*/var/lib/redis*|*/minio*|*/var/stellcodex*|*/var/www*)
      echo "RUNTIME"
      ;;
    *backup*|*/_backups*|*/backups/*|*/stellcodex_output/backups*)
      echo "BACKUP"
      ;;
    *archive*|*/archive_legacy*|*/_archive*)
      echo "ARCHIVE"
      ;;
    *log*|*/journal*|*/_jobs/logs*|*/evidence*)
      echo "LOG"
      ;;
    *dataset*|*/_datasets*|*/packages/datasets*)
      echo "DATASET"
      ;;
    *)
      echo "LEGACY"
      ;;
  esac
}

{
  echo "# Disk Audit (${TS})"
  echo
  echo "## Filesystem"
  df -h /
  echo
  echo "## Docker"
  docker system df 2>/dev/null || echo "docker system df unavailable"
  echo
  echo "## Directories Over 500MB"
  echo
  echo "| SizeBytes | Category | Path |"
  echo "|---:|---|---|"
  du -x -B1 -d 5 /root /var /tmp /minio /var/www 2>/dev/null \
    | awk '$1>=524288000 {print $1"\t"$2}' \
    | sort -nr \
    | while IFS=$'\t' read -r bytes path; do
        catg="$(categorize "$path")"
        echo "| ${bytes} | ${catg} | ${path} |"
      done
} > "${OUT}"

echo "${OUT}"

