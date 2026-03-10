# Güvenlik Politikası — Erişim Kontrolü

Son güncelleme: 2026-02-28

---

## Yetkili Kullanıcılar

WhatsApp kanalı:
- Yalnızca `STELL_OWNER_PHONE` (`.env` dosyasında tanımlı) numarası kabul edilir
- Diğer numaralardan gelen mesajlar yoksayılır veya "yetkisiz" yanıtı döner

---

## Gizli Bilgiler — Asla Paylaşma

- `storage_key` → asla response'a yazma
- API anahtarları (WHATSAPP_TOKEN, ANTHROPIC_API_KEY, vb.)
- DB şifreleri
- JWT secret
- `.env` içeriği

---

## İzin Verilen Komutlar (Onaysız Çalıştırılabilir)

```bash
# Okuma komutları
docker ps
pm2 list
df -h /
systemctl status nginx
docker logs <container> --tail 50
pm2 logs --lines 20

# Log okuma (read-only)
tail -f /var/log/nginx/access.log
```

---

## Onay Gerektiren Komutlar

```bash
# Veri değiştiren işlemler
docker restart <container>
pm2 restart <app>
systemctl reload nginx
docker-compose up --build

# DB işlemleri
psql UPDATE / DELETE / DROP

# Dosya silme
rm -rf
```

---

## Yasak İşlemler

- `rm -rf /` veya sistem dizinlerini silme
- Production DB'yi backup almadan değiştirme
- Credential bilgilerini log'a yazma
- Yetkisiz dış API'ye veri gönderme

---

## Log Politikası

- Her dış aksiyon (API çağrısı, komut çalıştırma) loglanır
- Log yolu: `/root/stell/genois/logs/`
- Log formatı: `[YYYY-MM-DD HH:MM] [ACTION] [RESULT]`
- Loglar 30 gün saklanır
