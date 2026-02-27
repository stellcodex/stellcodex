#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-stellcodex}"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUT_DIR"
FILE="$OUT_DIR/db_${DB_NAME}_${TS}.sql.gz"
echo "Creating DB dump: $FILE"
PGPASSWORD="${DB_PASSWORD:-}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "$FILE"
echo "PASS: db backup $FILE"
