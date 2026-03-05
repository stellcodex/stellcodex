#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 <block_name> <operation> <result> <next_step> [errors]" >&2
  exit 1
fi

block_name="$1"
operation="$2"
result="$3"
next_step="$4"
errors="${5:-}"

timestamp="$(date +%Y%m%d_%H%M%S)"
iso_now="$(date -Iseconds)"
backup_dir="/root/workspace/_backups/${timestamp}_${block_name}"
remote_dir="gdrive:stellcodex-genois/01_inbox/backups/${timestamp}_${block_name}/"
progress_file="/root/workspace/handoff/CODEX_PROGRESS.md"
evidence_log="/root/workspace/_runs/codex_execution.log"

mkdir -p "$backup_dir"/{pm2,docker,nginx,postgres,redis,health,system}

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$evidence_log" >/dev/null
}

run_capture() {
  local label="$1"
  shift
  log "capture:${label}: $*"
  if "$@" >"${backup_dir}/${label}.txt" 2>&1; then
    :
  else
    printf '\n[command failed with exit %s]\n' "$?" >>"${backup_dir}/${label}.txt"
  fi
}

copy_if_exists() {
  local src="$1"
  local dest="$2"
  if [[ -e "$src" ]]; then
    cp -a "$src" "$dest"
  fi
}

log "snapshot:start block=${block_name} dir=${backup_dir}"

run_capture system/uname uname -a
run_capture system/date date -Iseconds
run_capture system/uptime uptime
run_capture system/df df -h
run_capture system/free free -h
run_capture system/ports ss -lntp

run_capture pm2/list pm2 list
run_capture pm2/show_webhook pm2 show stell-webhook
run_capture pm2/show_next pm2 show stellcodex-next
run_capture pm2/show_listener pm2 show stell-event-listener
run_capture pm2/show_heartbeat pm2 show stell-heartbeat
run_capture pm2/show_bridge pm2 show stell-rpc-bridge
run_capture pm2/logs pm2 logs --lines 120 --nostream

run_capture docker/ps docker ps --no-trunc
run_capture docker/logs_backend docker logs --tail 120 stellcodex-backend
run_capture docker/logs_postgres docker logs --tail 80 stellcodex-postgres
run_capture docker/logs_redis docker logs --tail 80 stellcodex-redis
run_capture docker/logs_minio docker logs --tail 80 stellcodex-minio
run_capture docker/logs_worker docker logs --tail 120 stellcodex-worker

copy_if_exists /etc/nginx/nginx.conf "${backup_dir}/nginx/nginx.conf"
copy_if_exists /etc/nginx/sites-enabled/stellcodex "${backup_dir}/nginx/sites-enabled-stellcodex.conf"
copy_if_exists /etc/nginx/sites-available/stellcodex.conf "${backup_dir}/nginx/sites-available-stellcodex.conf"
copy_if_exists /var/www/stellcodex/infrastructure/nginx/stellcodex.conf "${backup_dir}/nginx/repo-stellcodex.conf"
run_capture nginx/test nginx -t

run_capture postgres/schema_dump docker exec stellcodex-postgres pg_dump -U stellcodex -d stellcodex --schema-only
run_capture postgres/tables docker exec stellcodex-postgres psql -U stellcodex -d stellcodex -c "\\dt"

run_capture redis/ping docker exec stellcodex-redis redis-cli ping
run_capture redis/stream_info docker exec stellcodex-redis redis-cli XINFO STREAM stell:events:stream
run_capture redis/stream_groups docker exec stellcodex-redis redis-cli XINFO GROUPS stell:events:stream
run_capture redis/keys docker exec stellcodex-redis redis-cli --scan --pattern 'stell:*'

run_capture health/root_https bash -lc "curl -k -sS -D - -H 'Host: stellcodex.com' https://127.0.0.1/ || true"
run_capture health/backend bash -lc "curl -sS -D - http://127.0.0.1:8000/api/v1/health || true"
run_capture health/webhook bash -lc "curl -sS -D - http://127.0.0.1:4500/stell/health || true"
run_capture health/public bash -lc "curl -sS -D - https://stellcodex.com/ || true"

run_capture system/tree bash -lc "find /root/workspace -maxdepth 2 -type d | sort"

log "snapshot:sync block=${block_name} remote=${remote_dir}"
if rclone sync "$backup_dir" "$remote_dir" >"${backup_dir}/system/rclone_sync.txt" 2>&1; then
  rclone lsl "$remote_dir" >"${backup_dir}/system/rclone_lsl.txt" 2>&1 || true
  sync_result="ok"
else
  sync_result="failed"
fi

cat >>"$progress_file" <<EOF
## ${iso_now} ${block_name}
time: ${iso_now}
operation: ${operation}
result: ${result}
errors: ${errors:-none}
backup location: ${backup_dir}
remote sync: ${remote_dir} (${sync_result})
next step: ${next_step}

EOF

cat >>"$evidence_log" <<EOF
[${iso_now}] snapshot:complete block=${block_name} dir=${backup_dir} remote=${remote_dir} sync=${sync_result}
[${iso_now}] progress:operation=${operation}
[${iso_now}] progress:result=${result}
[${iso_now}] progress:errors=${errors:-none}
[${iso_now}] progress:next=${next_step}
EOF

printf '%s\n' "$backup_dir"
