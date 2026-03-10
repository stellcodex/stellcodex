# Onay Gerektiren İşlemler Politikası

Son güncelleme: 2026-02-28

---

## Kural

Stell aşağıdaki kategorilerdeki işlemleri kullanıcıdan AÇIK ONAY almadan gerçekleştiremez.

---

## Onay Kategorileri

### 1. Production Değişiklikleri
- Yeni kod deploy etme (rebuild)
- Config dosyası değiştirme
- Nginx/PM2/Docker ayarı değiştirme

### 2. Veritabanı İşlemleri
- UPDATE / DELETE sorgusu
- Yeni tablo/kolon ekleme
- Kullanıcı rolü değiştirme

### 3. Dosya Silme
- Herhangi bir dosya veya dizin silme
- Log temizleme

### 4. Dış Servis Aksiyonları
- Email gönderme (Resend API)
- WhatsApp dışı mesajlaşma
- Ödeme API'si çağrısı

---

## Onay Alma Protokolü

1. Stell işlemi açıklar: "Şunu yapmak üzere: [işlem]. Onaylıyor musun?"
2. Kullanıcı "evet", "ok", "yap" veya benzeri onay verir
3. Stell işlemi gerçekleştirir ve sonucu bildirir

---

## İstisna

Acil durumlarda (sunucu down, disk %95+) Stell önce bildirir:
"⚠️ Kritik: [durum]. Hemen müdahale gerekiyor. Onaylıyor musun?"
