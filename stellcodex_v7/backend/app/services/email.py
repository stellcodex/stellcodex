"""
Email servisi — Resend API kullanır.
RESEND_API_KEY env değişkeni set edilince aktif olur.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("EMAIL_FROM", "Stellcodex <noreply@stellcodex.com>")
SITE_URL = os.getenv("SITE_URL", "https://stellcodex.com")


def _send(to: str, subject: str, html: str) -> bool:
    """Resend API ile email gönder. API key yoksa logla ve geç."""
    if not RESEND_API_KEY:
        log.warning("RESEND_API_KEY set edilmemiş, email gönderilmedi: %s → %s", to, subject)
        return False

    try:
        import httpx
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            log.info("Email gönderildi: %s → %s", to, subject)
            return True
        else:
            log.error("Resend hata: %s %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        log.exception("Email gönderme hatası: %s", e)
        return False


def send_welcome(to: str) -> bool:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">Stellcodex'e Hoş Geldiniz</h2>
      <p>Hesabınız başarıyla oluşturuldu.</p>
      <a href="{SITE_URL}/dashboard"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none;margin-top:16px">
        Panele Git
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        Stellcodex · stellcodex.com
      </p>
    </div>
    """
    return _send(to, "Stellcodex'e Hoş Geldiniz", html)


def send_invite(to: str, temp_password: str) -> bool:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">Stellcodex'e Davet Edildiniz</h2>
      <p>Hesabınız oluşturuldu. Aşağıdaki bilgilerle giriş yapabilirsiniz:</p>
      <div style="background:#f5f3ef;padding:16px;border-radius:8px;margin:16px 0">
        <div><strong>Email:</strong> {to}</div>
        <div><strong>Geçici şifre:</strong> {temp_password}</div>
      </div>
      <a href="{SITE_URL}/login"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none">
        Giriş Yap
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        Giriş yaptıktan sonra şifrenizi değiştirmenizi öneririz.
      </p>
    </div>
    """
    return _send(to, "Stellcodex'e Davet Edildiniz", html)


def send_password_reset(to: str, reset_token: str) -> bool:
    reset_url = f"{SITE_URL}/reset-password?token={reset_token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">Şifre Sıfırlama</h2>
      <p>Şifrenizi sıfırlamak için aşağıdaki butona tıklayın.
         Bu link 1 saat geçerlidir.</p>
      <a href="{reset_url}"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none;margin-top:16px">
        Şifremi Sıfırla
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        Bu isteği siz yapmadıysanız bu emaili görmezden gelin.
      </p>
    </div>
    """
    return _send(to, "Şifre Sıfırlama — Stellcodex", html)
