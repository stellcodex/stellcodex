#!/usr/bin/env bash
set -euo pipefail

# Force the distro-packaged compose dependencies instead of /usr/local overrides.
export PYTHONPATH=/usr/lib/python3/dist-packages

compose_args=("$@")
compose_dir=""

for ((i = 0; i < ${#compose_args[@]}; i++)); do
  if [[ "${compose_args[$i]}" == "-f" ]] && (( i + 1 < ${#compose_args[@]} )); then
    compose_file="${compose_args[$((i + 1))]}"
    if [[ "$compose_file" == /* ]]; then
      compose_dir="$(dirname "$compose_file")"
    fi
    break
  fi
done

if [[ -n "$compose_dir" ]]; then
  cd "$compose_dir"
fi

exec /usr/bin/docker-compose "${compose_args[@]}"
