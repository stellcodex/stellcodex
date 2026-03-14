#!/usr/bin/env bash
# ops/scripts/cleanup.sh
# Kural: Sunucu = sadece CPU işlemci. Büyük dosya kalıcı değil.
# Çalıştır: bash ops/scripts/cleanup.sh
# Cron: 30 2 * * * /root/workspace/ops/scripts/cleanup.sh >> /var/log/stellcodex-cleanup.log 2>&1
set -euo pipefail

LOG_PREFIX="[cleanup $(date '+%Y-%m-%d %H:%M:%S')]"
echo "$LOG_PREFIX Başlıyor..."

# 1. AI venv (CUDA/GPU libs — CPU sunucuda anlamsız, 7GB)
if [ -d /root/workspace/AI/.venv ]; then
  echo "$LOG_PREFIX AI/.venv siliniyor (~7GB)..."
  rm -rf /root/workspace/AI/.venv
fi

# 2. Frontend node_modules (CI'da npm ci ile yeniden kurulur)
for nm in /root/workspace/frontend/node_modules /var/www/stellcodex/frontend/node_modules; do
  if [ -d "$nm" ]; then
    echo "$LOG_PREFIX node_modules siliniyor: $nm"
    rm -rf "$nm"
  fi
done

# 3. _runs dizinleri — son 2'si korunur, gerisi gider
if [ -d /root/workspace/_runs ]; then
  COUNT=$(ls -d /root/workspace/_runs/*/ 2>/dev/null | wc -l)
  if [ "$COUNT" -gt 2 ]; then
    echo "$LOG_PREFIX _runs temizleniyor (${COUNT} → 2 korunur)..."
    ls -dt /root/workspace/_runs/*/ 2>/dev/null | tail -n +3 | xargs rm -rf
  fi
fi

# 4. Python bytecode cache
find /root/workspace -type d -name "__pycache__" \
  \( -not -path "*/.git/*" \) \
  -exec rm -rf {} + 2>/dev/null || true
find /root/workspace -name "*.pyc" \
  \( -not -path "*/.git/*" \) \
  -delete 2>/dev/null || true

# 5. Geçici build artefaktları
rm -rf \
  /root/workspace/_stage_patch_backend \
  /root/workspace/_stage_patch_frontend \
  /root/workspace/_tmp_build_id.txt \
  /tmp/stellcodex-backup-* \
  2>/dev/null || true

# 6. Docker dangling image + build cache
echo "$LOG_PREFIX Docker dangling image temizleniyor..."
docker image prune -f 2>/dev/null || true
docker builder prune -f 2>/dev/null || true

# 7. Sistem /tmp (1 günden eski dosyalar)
find /tmp -maxdepth 1 -type f -mtime +1 -delete 2>/dev/null || true

# 8. Eski log dosyaları (7 günden eski)
find /root/workspace/AI/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true

# 9. _models — Drive'a yüklendikten sonra kaldırılabilir (opsiyonel)
# Aktif kullanılan modeli silmiyoruz; sadece eski/çift olanları temizle
find /root/workspace/_models -name "*.bin.tmp" -delete 2>/dev/null || true

echo "$LOG_PREFIX Tamamlandı."
df -h / | tail -1 | awk -v p="$LOG_PREFIX" '{print p " Disk: "$5" kullanımda, "$4" boş"}'
