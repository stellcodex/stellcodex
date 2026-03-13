"""Email service backed by the Resend API.

The service becomes active only when ``RESEND_API_KEY`` is configured.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("EMAIL_FROM", "Stellcodex <noreply@stellcodex.com>")
SITE_URL = os.getenv("SITE_URL", "https://stellcodex.com")


def email_delivery_enabled() -> bool:
    return bool(RESEND_API_KEY)


def _send(to: str, subject: str, html: str) -> bool:
    """Send email through the Resend API and fail closed when disabled."""
    if not email_delivery_enabled():
        log.warning("RESEND_API_KEY is not configured, email was skipped: %s -> %s", to, subject)
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
            log.info("Email sent: %s -> %s", to, subject)
            return True
        else:
            log.error("Resend error: %s %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        log.exception("Email send failed: %s", e)
        return False


def send_welcome(to: str) -> bool:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">Welcome to Stellcodex</h2>
      <p>Your account has been created successfully.</p>
      <a href="{SITE_URL}/dashboard"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none;margin-top:16px">
        Open Dashboard
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        Stellcodex · stellcodex.com
      </p>
    </div>
    """
    return _send(to, "Welcome to Stellcodex", html)


def send_invite(to: str, temp_password: str) -> bool:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">You have been invited to Stellcodex</h2>
      <p>Your account is ready. Use the credentials below to sign in:</p>
      <div style="background:#f5f3ef;padding:16px;border-radius:8px;margin:16px 0">
        <div><strong>Email:</strong> {to}</div>
        <div><strong>Temporary password:</strong> {temp_password}</div>
      </div>
      <a href="{SITE_URL}/login"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none">
        Sign In
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        Change your password after the first login.
      </p>
    </div>
    """
    return _send(to, "You have been invited to Stellcodex", html)


def send_password_reset(to: str, reset_token: str) -> bool:
    reset_url = f"{SITE_URL}/reset-password?token={reset_token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#0c2a2a">Password Reset</h2>
      <p>Use the button below to reset your password.
         This link stays valid for 1 hour.</p>
      <a href="{reset_url}"
         style="display:inline-block;background:#0c2a2a;color:#fff;padding:10px 24px;
                border-radius:8px;text-decoration:none;margin-top:16px">
        Reset Password
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:32px">
        If you did not request this change, you can ignore this email.
      </p>
    </div>
    """
    return _send(to, "Password Reset — Stellcodex", html)
