# WhatsApp Kanal Politikası

Son güncelleme: 2026-02-28

---

## Teknik Detaylar

- **API:** Meta WhatsApp Cloud API v19.0
- **Webhook URL:** `https://stellcodex.com/stell/webhook`
- **Webhook Servisi:** FastAPI (`/root/stell/webhook/main.py`)
- **PM2 Servis:** `stell-webhook` (port 4500)
- **Veri dosyaları:** `.env` içinde (asla commit'leme)

---

## Güvenlik Kuralları

- Yalnızca `STELL_OWNER_PHONE` numarasından gelen mesajlar işlenir
- `WEBHOOK_VERIFY_TOKEN` Meta'ya kayıtlı, dışarıya paylaşma
- `WHATSAPP_TOKEN` 90 günde bir yenilenir (Meta yönetim panelinden)

---

## Mesaj Limitleri

- Tek mesaj maksimum: 4096 karakter
- Günde maksimum mesaj: Meta Business API limitine göre (tier'a bağlı)
- Uzun yanıtlar bölünür ve sırayla gönderilir

---

## Belge/Dosya İşleme

- Kullanıcı belge gönderirse → `/root/stell/genois/05_whatsapp_ingest/` klasörüne kaydet
- Dosya Meta API'den indirilir, yerel'e yazılır
- Kullanıcıya "Belge alındı: [dosya adı]" mesajı gönderilir

---

## PM2 Başlatma

```bash
pm2 start /root/stell/webhook/ecosystem.config.js
pm2 save
pm2 startup
```

## Nginx Proxy Ayarı

```nginx
location /stell/webhook {
    proxy_pass http://127.0.0.1:4500;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```
