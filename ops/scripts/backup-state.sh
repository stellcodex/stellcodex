#!/usr/bin/env bash
# ops/scripts/backup-state.sh
# State + DB + config → Google Drive
# Cron: 0 2 * * * /root/workspace/ops/scripts/backup-state.sh >> /var/log/stellcodex-backup.log 2>&1
set -euo pipefail

DRIVE_ROOT="gdrive:stellcodex-genois"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_PREFIX="[backup-state $TS]"
TMP="/tmp/stellcodex-backup-$$"
mkdir -p "$TMP"
trap "rm -rf $TMP" EXIT

echo "$LOG_PREFIX Başlıyor..."

# 1. PostgreSQL dump → Drive/backups/db/
echo "$LOG_PREFIX DB dump alınıyor..."
DB_CONTAINER="${DB_CONTAINER:-deploy_postgres_1}"
DB_USER="${POSTGRES_USER:-stellcodex}"
DB_NAME="${POSTGRES_DB:-stellcodex}"

if docker ps --format "{{.Names}}" | grep -q "^${DB_CONTAINER}$"; then
  DUMP="$TMP/db_${TS}.sql.gz"
  docker exec "$DB_CONTAINER" sh -c \
    "PGPASSWORD=\"\${POSTGRES_PASSWORD}\" pg_dump -U ${DB_USER} ${DB_NAME}" \
    | gzip > "$DUMP"
  rclone copy "$DUMP" "${DRIVE_ROOT}/backups/db/"
  echo "$LOG_PREFIX DB dump → Drive OK"

  # 30 günden eski dump'ları temizle
  rclone delete "${DRIVE_ROOT}/backups/db/" \
    --min-age 30d --include "db_*.sql.gz" 2>/dev/null || true
else
  echo "$LOG_PREFIX UYARI: $DB_CONTAINER çalışmıyor, DB dump atlandı."
fi

# 2. Orchestra runtime state → Drive/state/
echo "$LOG_PREFIX Orchestra state yedekleniyor..."
STATE="/root/workspace/ops/orchestra/state"
if [ -d "$STATE" ] && [ "$(ls -A "$STATE")" ]; then
  rclone sync "$STATE/" "${DRIVE_ROOT}/state/"
  echo "$LOG_PREFIX Orchestra state → Drive OK"
fi

# 3. Config dosyaları → Drive/backups/config/<TS>/
echo "$LOG_PREFIX Config backup..."
CFG="$TMP/cfg"
mkdir -p "$CFG"

# .env dosyaları (hassas — Drive'ı sadece sahip görmeli)
for f in /root/stell/.env /root/workspace/.env \
          /root/workspace/_runs/repo_remote_split_20260308T013854Z/orchestra/.env; do
  [ -f "$f" ] && cp "$f" "$CFG/$(echo $f | tr '/' '_').env" || true
done

# Temel config dosyaları
cp /root/workspace/ops/orchestra/litellm.config.yaml "$CFG/" 2>/dev/null || true

rclone copy "$CFG/" "${DRIVE_ROOT}/backups/config/${TS}/"

# En fazla 10 config backup tut
CONF_COUNT=$(rclone lsf "${DRIVE_ROOT}/backups/config/" --dirs-only 2>/dev/null | wc -l)
if [ "$CONF_COUNT" -gt 10 ]; then
  OLDEST=$(rclone lsf "${DRIVE_ROOT}/backups/config/" --dirs-only 2>/dev/null | sort | head -1)
  rclone purge "${DRIVE_ROOT}/backups/config/${OLDEST}" 2>/dev/null || true
  echo "$LOG_PREFIX Eski config backup silindi: $OLDEST"
fi
echo "$LOG_PREFIX Config → Drive OK"

# 4. Knowledge base → Drive/knowledge/
echo "$LOG_PREFIX Knowledge sync..."
[ -d /root/workspace/_knowledge ] && \
  rclone sync /root/workspace/_knowledge/ "${DRIVE_ROOT}/knowledge/" 2>/dev/null || true
[ -d /root/stell/knowledge ] && \
  rclone sync /root/stell/knowledge/ "${DRIVE_ROOT}/knowledge/stell/" 2>/dev/null || true
echo "$LOG_PREFIX Knowledge OK"

echo "$LOG_PREFIX Tüm backup tamamlandı."
