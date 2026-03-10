#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <target-path>" >&2
  exit 2
fi

target="$(readlink -f "$1" 2>/dev/null || true)"
if [[ -z "${target}" ]]; then
  echo "DENY unresolved path: $1"
  exit 1
fi

allow_prefixes=(
  "/root/workspace/_truth"
  "/tmp"
  "/var/log"
)

for p in "${allow_prefixes[@]}"; do
  if [[ "${target}" == "${p}"* ]]; then
    echo "ALLOW ${target}"
    exit 0
  fi
done

echo "DENY ${target}"
exit 1

