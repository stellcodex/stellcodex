#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/root/workspace}"

require_path() {
  local p="$1"
  if [[ ! -e "$p" ]]; then
    echo "MISSING: $p" >&2
    return 1
  fi
}

check_boundary() {
  local name="$1"
  local base="$ROOT/$name"
  local ok=1
  for sub in src docs deploy scripts tests; do
    if ! require_path "$base/$sub"; then
      ok=0
    fi
  done
  if [[ "$ok" -eq 1 ]]; then
    echo "PASS $name"
  else
    echo "FAIL $name"
    return 1
  fi
}

check_boundary "stell-ai"
check_boundary "orchestra"
check_boundary "stellcodex"
check_boundary "infra"

echo "PASS all-boundaries"
