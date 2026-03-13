#!/usr/bin/env bash

stellcodex_acquire_lock() {
  local lock_name="$1"
  local wait_seconds="${2:-0}"
  local lock_root="${STELLCODEX_LOCK_ROOT:-/root/workspace/_runtime/locks}"
  local lock_file

  mkdir -p "${lock_root}"
  lock_file="${lock_root}/${lock_name}.lock"

  exec {STELLCODEX_LOCK_FD}> "${lock_file}"
  export STELLCODEX_LOCK_FD

  if (( wait_seconds > 0 )); then
    flock -w "${wait_seconds}" "${STELLCODEX_LOCK_FD}"
    return $?
  fi

  flock -n "${STELLCODEX_LOCK_FD}"
}
