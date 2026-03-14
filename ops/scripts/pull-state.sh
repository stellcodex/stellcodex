#!/usr/bin/env bash
# ops/scripts/pull-state.sh
# Drive'dan state çek (deploy öncesi veya disaster recovery)
# Kullanım: bash ops/scripts/pull-state.sh
set -euo pipefail

DRIVE_ROOT="gdrive:stellcodex-genois"
LOG_PREFIX="[pull-state $(date '+%Y-%m-%d %H:%M:%S')]"

echo "$LOG_PREFIX Drive'dan state çekiliyor..."

# 1. Orchestra runtime state
echo "$LOG_PREFIX Orchestra state..."
mkdir -p /root/workspace/ops/orchestra/state
rclone sync "${DRIVE_ROOT}/state/" \
  /root/workspace/ops/orchestra/state/ \
  --exclude ".archive/**"
echo "$LOG_PREFIX Orchestra state OK"

# 2. Knowledge base
echo "$LOG_PREFIX Knowledge base..."
mkdir -p /root/workspace/_knowledge
rclone sync "${DRIVE_ROOT}/knowledge/" \
  /root/workspace/_knowledge/ \
  --exclude "stell/**"
mkdir -p /root/stell/knowledge
rclone sync "${DRIVE_ROOT}/knowledge/stell/" \
  /root/stell/knowledge/ 2>/dev/null || true
echo "$LOG_PREFIX Knowledge OK"

# 3. ML modeli (sadece yoksa indir)
MODEL_DIR="/root/workspace/_models"
if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR 2>/dev/null)" ]; then
  echo "$LOG_PREFIX ML modeli Drive'dan indiriliyor..."
  mkdir -p "$MODEL_DIR"
  rclone copy "${DRIVE_ROOT}/backups/models/" "$MODEL_DIR/"
  echo "$LOG_PREFIX Model OK"
else
  echo "$LOG_PREFIX ML modeli zaten mevcut, atlanıyor."
fi

# 4. Mevcut DB backup listesi (restore manuel yapılır)
echo ""
echo "$LOG_PREFIX Mevcut DB yedekleri:"
rclone lsf "${DRIVE_ROOT}/backups/db/" 2>/dev/null | tail -5 || echo "  (yedek bulunamadı)"
echo ""
echo "$LOG_PREFIX Pull tamamlandı."
echo "DB restore için:"
echo "  rclone copy ${DRIVE_ROOT}/backups/db/<dosya>.sql.gz /tmp/"
echo "  gunzip -c /tmp/<dosya>.sql.gz | docker exec -i deploy_postgres_1 psql -U stellcodex"
