from __future__ import annotations

import json
from typing import TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthError(RuntimeError):
    pass


class GoogleProfile(TypedDict):
    sub: str
    email: str
    full_name: str | None


def _read_json(request: Request) -> dict:
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError) as exc:
        raise GoogleOAuthError("Google OAuth request failed") from exc
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GoogleOAuthError("Google OAuth response was invalid") from exc


def build_google_authorize_url(*, redirect_uri: str, state: str) -> str:
    if not settings.google_client_id:
        raise GoogleOAuthError("Google OAuth is not configured")
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
            "access_type": "online",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code_for_profile(*, code: str, redirect_uri: str) -> GoogleProfile:
    if not settings.google_client_id or not settings.google_client_secret:
        raise GoogleOAuthError("Google OAuth is not configured")

    token_request = Request(
        GOOGLE_TOKEN_URL,
        data=urlencode(
            {
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    token_payload = _read_json(token_request)
    access_token = str(token_payload.get("access_token") or "").strip()
    if not access_token:
        raise GoogleOAuthError("Google token exchange returned no access token")

    profile_request = Request(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    profile_payload = _read_json(profile_request)

    email = str(profile_payload.get("email") or "").strip().lower()
    sub = str(profile_payload.get("sub") or "").strip()
    full_name = str(profile_payload.get("name") or "").strip() or None
    email_verified = bool(profile_payload.get("email_verified"))
    if not email or not sub or not email_verified:
        raise GoogleOAuthError("Google account email is unavailable or unverified")

    return GoogleProfile(sub=sub, email=email, full_name=full_name)
