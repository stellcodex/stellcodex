#!/usr/bin/env bash
set -euo pipefail

CRON_FILE="${1:-/root/workspace/ops/cron/stellcodex-cleanup.cron}"
LOGROTATE_SRC="${LOGROTATE_SRC:-/root/workspace/ops/logrotate/stellcodex-runtime.conf}"
LOGROTATE_DEST="${LOGROTATE_DEST:-/etc/logrotate.d/stellcodex-runtime}"

if [ ! -f "${CRON_FILE}" ]; then
  echo "Missing cron file: ${CRON_FILE}" >&2
  exit 1
fi

TMP="$(mktemp)"
FILTERED="$(mktemp)"
trap 'rm -f "${TMP}" "${FILTERED}"' EXIT

crontab -l 2>/dev/null > "${TMP}" || true

grep -Fv "/root/workspace/ops/scripts/cleanup.sh" "${TMP}" \
  | grep -Fv "/root/workspace/ops/scripts/backup-state.sh" \
  | grep -Fv "/usr/sbin/logrotate -s /var/lib/logrotate/status-stellcodex /etc/logrotate.d/stellcodex-runtime" \
  | grep -Fv "docker image prune -af" \
  > "${FILTERED}" || true
mv "${FILTERED}" "${TMP}"

while IFS= read -r line; do
  case "${line}" in
    ""|\#*)
      continue
      ;;
  esac
  grep -Fqx "${line}" "${TMP}" || printf '%s\n' "${line}" >> "${TMP}"
done < "${CRON_FILE}"

if [ -f "${LOGROTATE_SRC}" ]; then
  install -m 0644 "${LOGROTATE_SRC}" "${LOGROTATE_DEST}"
  if command -v logrotate >/dev/null 2>&1; then
    logrotate -d "${LOGROTATE_DEST}" >/dev/null
  fi
  echo "Installed logrotate config: ${LOGROTATE_DEST}"
fi

crontab "${TMP}"

echo "Installed cleanup cron entries:"
grep -E "logrotate -s /var/lib/logrotate/status-stellcodex|backup-state.sh|cleanup.sh|docker image prune -af" "${TMP}" || true
