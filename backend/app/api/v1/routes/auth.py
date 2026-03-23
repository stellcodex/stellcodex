from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.security.jwt import clear_session_cookie, create_oauth_state_token, create_user_token, decode_token, set_session_cookie
from app.services.auth_access import upsert_google_user
from app.services.google_oauth import (
    GoogleOAuthError,
    build_google_authorize_url,
    exchange_code_for_profile,
)

router = APIRouter(tags=["auth"])


def _is_secure_request(request: Request) -> bool:
    forwarded_proto = str(request.headers.get("x-forwarded-proto") or "").strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"
    return request.url.scheme == "https"


def _base_site_url(request: Request) -> str:
    configured = str(settings.site_url or "").strip().rstrip("/")
    if configured:
        return configured
    forwarded_host = str(request.headers.get("x-forwarded-host") or request.headers.get("host") or "").strip()
    scheme = str(request.headers.get("x-forwarded-proto") or request.url.scheme or "https").strip()
    if not forwarded_host:
        raise HTTPException(status_code=500, detail="Unable to resolve application origin")
    return f"{scheme}://{forwarded_host}"


def _google_callback_url(request: Request) -> str:
    configured = str(settings.google_redirect_uri or "").strip().rstrip("/")
    if configured:
        return configured
    return f"{_base_site_url(request)}/api/v1/auth/google/callback"


def _safe_redirect_path(value: str | None) -> str:
    candidate = str(value or "/dashboard").strip() or "/dashboard"
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/dashboard"
    return candidate


def _sign_in_error_url(request: Request, code: str, redirect_to: str | None = None) -> str:
    query = {"auth": code}
    safe_redirect = _safe_redirect_path(redirect_to)
    if safe_redirect != "/dashboard":
        query["next"] = safe_redirect
    return f"{_base_site_url(request)}/sign-in?{urlencode(query)}"


def _decode_redirect_from_state(state_value: str | None) -> str | None:
    token = str(state_value or "").strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if payload.get("typ") != "oauth_state":
        return None
    return _safe_redirect_path(payload.get("redirect_to"))


def _clear_google_state_cookie(response: RedirectResponse, *, secure: bool) -> None:
    response.delete_cookie(
        key=settings.auth_google_state_cookie_name,
        httponly=True,
        samesite="lax",
        path="/",
        secure=secure,
    )

@router.get("/auth/google/start")
def google_start(request: Request, next: str | None = Query(default="/dashboard")):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")

    redirect_to = _safe_redirect_path(next)
    state = create_oauth_state_token(redirect_to)
    authorize_url = build_google_authorize_url(redirect_uri=_google_callback_url(request), state=state)
    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=settings.auth_google_state_cookie_name,
        value=state,
        max_age=settings.auth_google_state_ttl_minutes * 60,
        httponly=True,
        samesite="lax",
        path="/",
        secure=_is_secure_request(request),
    )
    return response


@router.get("/auth/google/callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    secure = _is_secure_request(request)
    fallback_redirect = _decode_redirect_from_state(state or request.cookies.get(settings.auth_google_state_cookie_name))
    if error:
        response = RedirectResponse(url=_sign_in_error_url(request, "google-denied", fallback_redirect), status_code=status.HTTP_302_FOUND)
        _clear_google_state_cookie(response, secure=secure)
        clear_session_cookie(response, secure=secure)
        return response

    if not code or not state:
        response = RedirectResponse(url=_sign_in_error_url(request, "google-missing", fallback_redirect), status_code=status.HTTP_302_FOUND)
        _clear_google_state_cookie(response, secure=secure)
        clear_session_cookie(response, secure=secure)
        return response

    state_cookie = str(request.cookies.get(settings.auth_google_state_cookie_name) or "").strip()
    if not state_cookie or state_cookie != state:
        response = RedirectResponse(url=_sign_in_error_url(request, "google-state", fallback_redirect), status_code=status.HTTP_302_FOUND)
        _clear_google_state_cookie(response, secure=secure)
        clear_session_cookie(response, secure=secure)
        return response

    redirect_to = _decode_redirect_from_state(state_cookie) or "/dashboard"
    try:
        payload = decode_token(state)
        if payload.get("typ") != "oauth_state":
            raise GoogleOAuthError("Invalid OAuth state")
        redirect_to = _safe_redirect_path(payload.get("redirect_to"))
        profile = exchange_code_for_profile(code=code, redirect_uri=_google_callback_url(request))
        user = upsert_google_user(
            db,
            email=profile["email"],
            google_sub=profile["sub"],
            full_name=profile.get("full_name"),
        )
    except Exception:
        response = RedirectResponse(url=_sign_in_error_url(request, "google-failed", redirect_to), status_code=status.HTTP_302_FOUND)
        _clear_google_state_cookie(response, secure=secure)
        clear_session_cookie(response, secure=secure)
        return response

    token = create_user_token(str(user.id), user.role, ttl_minutes=settings.auth_session_ttl_minutes)
    response = RedirectResponse(url=f"{_base_site_url(request)}{redirect_to}", status_code=status.HTTP_302_FOUND)
    _clear_google_state_cookie(response, secure=secure)
    set_session_cookie(response, token, secure=secure)
    return response
