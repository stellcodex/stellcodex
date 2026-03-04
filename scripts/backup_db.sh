#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-stellcodex}"
DB_NAME="${DB_NAME:-stellcodex}"
DB_CONTAINER="${DB_CONTAINER:-stellcodex-postgres}"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUT_DIR"
FILE="$OUT_DIR/db_${DB_NAME}_${TS}.sql.gz"
echo "Creating DB dump: $FILE"
TMP_SQL="$(mktemp)"
TMP_ERR="$(mktemp)"
cleanup() {
  rm -f "$TMP_SQL" "$TMP_ERR"
}
trap cleanup EXIT

run_local_dump() {
  PGPASSWORD="${DB_PASSWORD:-}" \
    pg_dump --no-password -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
}

run_container_dump() {
  docker exec "$DB_CONTAINER" sh -lc \
    "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; pg_dump --no-password -h localhost -p 5432 -U \"$DB_USER\" \"$DB_NAME\""
}

if run_local_dump >"$TMP_SQL" 2>"$TMP_ERR"; then
  :
elif command -v docker >/dev/null 2>&1 && docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
  echo "Local pg_dump failed; retrying with containerized pg_dump from ${DB_CONTAINER}" >&2
  if ! run_container_dump >"$TMP_SQL" 2>"$TMP_ERR"; then
    cat "$TMP_ERR" >&2
    exit 1
  fi
else
  cat "$TMP_ERR" >&2
  exit 1
fi

gzip -c "$TMP_SQL" > "$FILE"
echo "PASS: db backup $FILE"
