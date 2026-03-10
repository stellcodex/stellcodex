#!/usr/bin/env bash
set -euo pipefail

# Sacred Storage write-policy watchdog.
# Flags STELLCODEX process writable file descriptors outside:
#   - /root/workspace/_truth
#   - /tmp
#   - /var/log

MODE="${1:-oneshot}"
INTERVAL_SECONDS="${WATCHDOG_INTERVAL_SECONDS:-60}"
LOG_DIR="/var/log"
LOG_FILE="${LOG_DIR}/sacred_storage_write_watchdog.log"
STATE_FILE="/tmp/sacred_storage_write_watchdog.last"
REPORT_DIR="/root/workspace/_truth/12_reports"
ALLOWED_PREFIXES=(
  "/root/workspace/_truth/"
  "/tmp/"
  "/var/log/"
)
SCOPE_PATTERNS=(
  "/root/workspace"
  "/var/www/stellcodex"
  "/root/stell"
)

mkdir -p "${LOG_DIR}" "${REPORT_DIR}"
touch "${LOG_FILE}" "${STATE_FILE}"

in_scope() {
  local cmd="$1"
  local pat
  for pat in "${SCOPE_PATTERNS[@]}"; do
    if [[ "${cmd}" == *"${pat}"* ]]; then
      return 0
    fi
  done
  return 1
}

allowed_path() {
  local p="$1"
  local allowed
  for allowed in "${ALLOWED_PREFIXES[@]}"; do
    if [[ "${p}" == "${allowed}"* ]]; then
      return 0
    fi
  done
  return 1
}

skip_target() {
  local t="$1"
  [[ -z "${t}" ]] && return 0
  [[ "${t}" == pipe:* ]] && return 0
  [[ "${t}" == socket:* ]] && return 0
  [[ "${t}" == anon_inode:* ]] && return 0
  [[ "${t}" == /dev/* ]] && return 0
  [[ "${t}" == /proc/* ]] && return 0
  [[ "${t}" == /sys/* ]] && return 0
  [[ "${t}" != /* ]] && return 0
  return 1
}

scan_once() {
  local now
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local findings=0
  local pid proc cmd fd fdnum info flags access target key

  for proc in /proc/[0-9]*; do
    pid="${proc#/proc/}"
    [[ -r "${proc}/cmdline" ]] || continue
    cmd="$(tr '\0' ' ' < "${proc}/cmdline" 2>/dev/null || true)"
    [[ -n "${cmd}" ]] || continue
    in_scope "${cmd}" || continue

    for fd in "${proc}"/fd/*; do
      [[ -e "${fd}" ]] || continue
      fdnum="${fd##*/}"
      info="${proc}/fdinfo/${fdnum}"
      [[ -r "${info}" ]] || continue
      flags="$(awk '/^flags:/ {print $2}' "${info}" 2>/dev/null || true)"
      [[ -n "${flags}" ]] || continue
      # flags are octal; lower 2 bits are access mode: 0=RDONLY,1=WRONLY,2=RDWR
      access="$((8#${flags} & 3))"
      [[ "${access}" -ne 0 ]] || continue

      target="$(readlink "${fd}" 2>/dev/null || true)"
      skip_target "${target}" && continue
      target="$(readlink -f "${fd}" 2>/dev/null || echo "${target}")"
      allowed_path "${target}" && continue

      key="${pid}|${fdnum}|${target}"
      if ! grep -Fqx "${key}" "${STATE_FILE}"; then
        findings=$((findings + 1))
        printf '%s violation pid=%s fd=%s path=%q cmd=%q\n' \
          "${now}" "${pid}" "${fdnum}" "${target}" "${cmd}" | tee -a "${LOG_FILE}" >/dev/null
        echo "${key}" >> "${STATE_FILE}"
      fi
    done
  done

  if [[ "${findings}" -gt 0 ]]; then
    printf '%s findings=%s\n' "${now}" "${findings}" >> "${REPORT_DIR}/write_policy_findings.log"
  else
    printf '%s findings=0\n' "${now}" >> "${REPORT_DIR}/write_policy_findings.log"
  fi
}

case "${MODE}" in
  oneshot)
    scan_once
    ;;
  daemon)
    while true; do
      scan_once
      sleep "${INTERVAL_SECONDS}"
    done
    ;;
  *)
    echo "usage: $0 [oneshot|daemon]" >&2
    exit 2
    ;;
esac
