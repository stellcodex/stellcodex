# Admin Operasyon Playbook

Son güncelleme: 2026-02-28

---

## Servis Restart Prosedürleri

### Backend restart
```bash
cd /var/www/stellcodex
docker-compose -f infrastructure/deploy/docker-compose.yml restart stellcodex-backend
```

### Frontend restart
```bash
pm2 restart stellcodex-next
```

### Tüm servisleri yeniden başlat
```bash
cd /var/www/stellcodex
docker-compose -f infrastructure/deploy/docker-compose.yml up -d
pm2 restart stellcodex-next
```

### Nginx reload
```bash
systemctl reload nginx
```

---

## Rebuild Prosedürü (Kod Değişikliği Sonrası)

```bash
# Backend rebuild
cd /var/www/stellcodex
docker-compose -f infrastructure/deploy/docker-compose.yml up -d --build stellcodex-backend

# Frontend rebuild (PM2 restart yeterli değilse)
cd /var/www/stellcodex/frontend
npm run build
pm2 restart stellcodex-next
```

---

## Yeni Kullanıcı Ekleme

```bash
# API üzerinden
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "GucluSifre123!", "name": "Ad Soyad"}'

# Doğrudan DB üzerinden (son çare)
docker exec -it stellcodex-postgres psql -U stellcodex -d stellcodex \
  -c "UPDATE users SET role='admin' WHERE email='user@example.com';"
```

---

## Log İzleme

```bash
# Backend canlı log
docker logs -f stellcodex-backend --tail 50

# Worker log
docker logs -f stellcodex-worker --tail 50

# Nginx access log
tail -f /var/log/nginx/access.log

# Nginx error log
tail -f /var/log/nginx/error.log
```

---

## Disk Temizliği

```bash
# Docker kullanılmayan image/container temizle
docker system prune -f

# Disk kullanım özeti
df -h /
du -sh /var/www/stellcodex/
```

---

## Onay Gerektiren İşlemler

Bu işlemler WhatsApp veya başka kanaldan yapılmadan önce kullanıcıdan ONAY alınmalıdır:

- Production DB'ye yazma (UPDATE/DELETE)
- Yeni deploy / rebuild
- Kullanıcı silme
- Servis durdurma
