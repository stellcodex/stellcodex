# WhatsApp Komut Listesi — Stell

Son güncelleme: 2026-02-28

---

## Temel Komutlar

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `durum` | Platform servis durumu | `durum` |
| `yardım` | Komut listesi | `yardım` |
| `not: <metin>` | Not kaydet | `not: Müşteri A ile Cuma görüşme` |
| `notlar` | Son notları listele | `notlar` |
| `merhaba` / `selam` | Selamlama | `merhaba` |

---

## AI Model Komutları

| Komut | Açıklama |
|-------|----------|
| `claude: <görev>` | Claude Code'a gönder |
| `gemini: <görev>` | Gemini'ye gönder |
| `codex: <görev>` | OpenAI Codex'e gönder |
| `abacus: <görev>` | Abacus AI'ya gönder |

---

## Stellcodex Admin Komutları

| Komut | Açıklama |
|-------|----------|
| `servisler` | Docker + PM2 servis listesi |
| `log: backend` | Backend son 20 satır log |
| `log: frontend` | Frontend son 20 satır log |
| `log: worker` | Worker son 20 satır log |
| `disk` | Disk kullanımı |

---

## Dosya Komutları

| Komut | Açıklama |
|-------|----------|
| `drive sync` | Drive'dan son dosyaları çek |
| `drive listele` | Drive inbox listesi |

---

## Akış Kuralları

1. Mesaj sadece `STELL_OWNER_PHONE` numarasından geliyorsa işlenir
2. Bilinmeyen komut → Claude'a gönder (genel LLM yanıtı)
3. Dosya gelirse → `05_whatsapp_ingest/` klasörüne kaydet
4. Her aksiyondan sonra log yaz: `/root/stell/genois/logs/`
