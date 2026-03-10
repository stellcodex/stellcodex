# AI Delegasyon Playbook

Son güncelleme: 2026-02-28

---

## Genel Kural

Kullanıcı mesajında prefix varsa → o modele ilet.
Prefix yoksa → içerik analizine göre otomatik yönlendir.
Belirsizse → Stell kendisi yanıtlar.

---

## Claude Code Entegrasyonu

**API:** Anthropic API (claude-sonnet-4-6)
**Config:** `~/.claude/`
**Kullanım Alanı:** Kod yazma, mimari, debug, refactor, sistem analizi

```python
# Örnek delegasyon
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    system=open("/root/stell/prompts/system/stell-core.md").read(),
    messages=[{"role": "user", "content": user_message}]
)
```

---

## Gemini / AITK Entegrasyonu

**Config:** `~/.aitk/`
**Komut:** `aitk`
**Kullanım Alanı:** Uzun doküman analizi, PDF okuma, dosya işleme

---

## Codex Entegrasyonu

**Config:** `~/.codex/`
**Model:** gpt-5.3-codex
**Kullanım Alanı:** Hızlı snippet üretimi, basit kod soruları

---

## Handoff Protokolü

Her delegasyon sonrası:
1. `/root/workspace/handoff/<model>-status.md` güncelle
2. Görevi, sonucu ve timestamp'i yaz
3. Hata varsa hata mesajını kaydet

Örnek handoff içeriği:
```markdown
## Görev
claude: login endpoint debug

## Durum
Tamamlandı

## Sonuç Özeti
Bcrypt import eksikti. requirements.txt güncellendi, rebuild yapıldı.

## Timestamp
2026-02-28 14:30
```

---

## Hata Yönetimi

- Model yanıt vermezse → kullanıcıya "Model şu an yanıt vermiyor, tekrar dene" bildir
- Timeout → 30 sn bekleme, sonra hata mesajı
- API limit aşımı → sıradaki modele yönlendir (fallback)
