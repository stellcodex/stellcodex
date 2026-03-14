#!/usr/bin/env bash
# ops/scripts/deploy.sh
# Tam deploy: state çek → container güncelle → backup → temizle
# Kullanım: IMAGE_TAG=sha-abc1234 bash ops/scripts/deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="[deploy $(date '+%Y-%m-%d %H:%M:%S')]"
IMAGE_TAG="${IMAGE_TAG:-latest}"
COMPOSE_FILE="${COMPOSE_FILE:-/root/workspace/ops/deploy/docker-compose.ghcr.yml}"

echo "$LOG_PREFIX Deploy başlıyor... IMAGE_TAG=$IMAGE_TAG"

# 1. Drive'dan state çek
echo "$LOG_PREFIX State çekiliyor..."
bash "$SCRIPT_DIR/pull-state.sh"

# 2. GHCR'dan image çek
echo "$LOG_PREFIX Image çekiliyor: ghcr.io/stellcodex/stellcodex-backend:$IMAGE_TAG"
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" pull backend worker 2>&1 || {
  echo "$LOG_PREFIX UYARI: GHCR pull başarısız — mevcut image kullanılıyor"
}

# 3. Container'ları güncelle (sıfır kesinti için rolling restart)
echo "$LOG_PREFIX Container'lar güncelleniyor..."
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" up -d \
  --no-build --remove-orphans

# 4. Sağlık kontrolü
echo "$LOG_PREFIX Sağlık kontrolü..."
for i in $(seq 1 12); do
  STATUS=$(curl -s --max-time 5 http://localhost:18000/api/v1/health 2>/dev/null || echo "fail")
  if echo "$STATUS" | grep -q '"status":"ok"'; then
    echo "$LOG_PREFIX Backend healthy ✓"
    break
  fi
  [ $i -eq 12 ] && { echo "$LOG_PREFIX HATA: Backend sağlıklı değil!"; exit 1; }
  echo "$LOG_PREFIX Bekleniyor ($i/12)..."
  sleep 10
done

# 5. State backup (deploy sonrası anında yedek)
echo "$LOG_PREFIX Deploy sonrası yedek alınıyor..."
bash "$SCRIPT_DIR/backup-state.sh"

# 6. Temizlik
echo "$LOG_PREFIX Temizlik..."
bash "$SCRIPT_DIR/cleanup.sh"

echo "$LOG_PREFIX Deploy tamamlandı. IMAGE_TAG=$IMAGE_TAG"
