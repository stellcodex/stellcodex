import inspect
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("DATABASE_URL", "sqlite:///./access-model-test.db")
os.environ.setdefault("JWT_SECRET", "12345678901234567890123456789012")

from fastapi import HTTPException, Request, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.routes.auth import google_start
from app.api.v1.routes.me import me as me_route
from app.api.v1.routes.platform_contract import auth_logout as logout_route
from app.api.v1.routes.share import resolve_share_short_alias
from app.api.v1.routes.users import LoginIn, login as login_route
from app.core.config import settings
from app.db.base import Base
from app.models.user import PasswordResetToken, RevokedToken, User
from app.security.deps import get_optional_principal, require_role
from app.security.jwt import create_user_token
from app.services.auth_access import hash_password, set_user_active, upsert_google_user


def build_session_factory(database_path: Path) -> tuple[sessionmaker, object]:
    engine = create_engine(f"sqlite:///{database_path}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine, tables=[User.__table__, PasswordResetToken.__table__, RevokedToken.__table__])
    return SessionLocal, engine


def build_request(*, cookie_token: str | None = None, authorization_token: str | None = None, path: str = "/auth/me") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    headers.append((b"host", b"testserver"))
    if cookie_token:
        headers.append((b"cookie", f"{settings.auth_session_cookie_name}={cookie_token}".encode("utf-8")))
    if authorization_token:
        headers.append((b"authorization", f"Bearer {authorization_token}".encode("utf-8")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope)


def seed_user(session_factory: sessionmaker, *, email: str, password: str, role: str) -> User:
    db = session_factory()
    try:
        user = User(
            email=email,
            full_name=email.split("@", 1)[0].title(),
            password_hash=hash_password(password),
            role=role,
            auth_provider="local",
        )
        set_user_active(user, True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def issue_token(user: User) -> str:
    return create_user_token(str(user.id), user.role, ttl_minutes=settings.auth_session_ttl_minutes)


def check_local_login_success(session_factory: sessionmaker) -> None:
    user = seed_user(session_factory, email="member@example.com", password="MemberPass123!", role="member")
    db = session_factory()
    try:
        request = build_request(path="/auth/login")
        response = Response()
        result = login_route(
            data=LoginIn(email=user.email, password="MemberPass123!"),
            request=request,
            response=response,
            db=db,
        )
        payload = result.model_dump()

        assert payload["email"] == user.email
        assert payload["role"] == "member"
        assert payload["session"]["authenticated"] is True
        assert payload["session"]["user"]["role"] == "member"
        assert settings.auth_session_cookie_name in response.headers.get("set-cookie", "")
    finally:
        db.close()


def check_logout_success(session_factory: sessionmaker) -> None:
    user = seed_user(session_factory, email="logout@example.com", password="LogoutPass123!", role="member")
    token = issue_token(user)
    db = session_factory()
    try:
        me_before = me_route(principal=get_optional_principal(build_request(cookie_token=token), db=db), db=db)
        response = Response()
        logout_route(request=build_request(cookie_token=token, path="/auth/logout"), response=response, db=db)

        assert me_before["authenticated"] is True
        assert settings.auth_session_cookie_name in response.headers.get("set-cookie", "")
        assert "Max-Age=0" in response.headers.get("set-cookie", "")

        try:
            get_optional_principal(build_request(cookie_token=token), db=db)
            raise AssertionError("revoked session token should be rejected")
        except HTTPException as exc:
            assert exc.status_code == 401
    finally:
        db.close()


def check_auth_me_role_resolution(session_factory: sessionmaker) -> None:
    member = seed_user(session_factory, email="member-role@example.com", password="MemberRole123!", role="member")
    admin = seed_user(session_factory, email="admin-role@example.com", password="AdminRole123!", role="admin")
    db = session_factory()
    try:
        anonymous = me_route(principal=get_optional_principal(build_request(), db=db), db=db)
        member_payload = me_route(principal=get_optional_principal(build_request(cookie_token=issue_token(member)), db=db), db=db)
        admin_payload = me_route(principal=get_optional_principal(build_request(cookie_token=issue_token(admin)), db=db), db=db)

        assert anonymous == {"authenticated": False, "role": None, "user": None}
        assert member_payload["role"] == "member"
        assert admin_payload["role"] == "admin"
    finally:
        db.close()


def check_google_auto_registration_defaults_to_member(session_factory: sessionmaker) -> None:
    previous = settings.google_admin_whitelist_raw
    settings.google_admin_whitelist_raw = ""
    db = session_factory()
    try:
        user = upsert_google_user(
            db,
            email="new-google-user@example.com",
            google_sub="google-sub-1",
            full_name="Google Member",
        )
        assert user.role == "member"
        assert user.auth_provider == "google"
        assert user.google_sub == "google-sub-1"
    finally:
        settings.google_admin_whitelist_raw = previous
        db.close()


def check_google_admin_whitelist_behavior(session_factory: sessionmaker) -> None:
    previous = settings.google_admin_whitelist_raw
    settings.google_admin_whitelist_raw = "whitelist-admin@example.com"
    db = session_factory()
    try:
        user = upsert_google_user(
            db,
            email="whitelist-admin@example.com",
            google_sub="google-sub-2",
            full_name="Whitelisted Admin",
        )
        assert user.role == "admin"
        assert user.auth_provider == "google"
    finally:
        settings.google_admin_whitelist_raw = previous
        db.close()


def check_google_start_uses_redirect_when_env_present() -> None:
    previous_client_id = settings.google_client_id
    previous_client_secret = settings.google_client_secret
    previous_redirect_uri = settings.google_redirect_uri
    previous_site_url = settings.site_url
    settings.google_client_id = "test-google-client-id"
    settings.google_client_secret = "test-google-client-secret"
    settings.google_redirect_uri = "https://stellcodex.test/api/v1/auth/google/callback"
    settings.site_url = "https://stellcodex.test"

    try:
        response = google_start(request=build_request(path="/auth/google/start"), next="/files/scx_test-file-id/viewer")
        location = response.headers.get("location", "")
        set_cookie = response.headers.get("set-cookie", "")

        assert response.status_code == 302
        assert "accounts.google.com" in location
        assert "client_id=test-google-client-id" in location
        assert "redirect_uri=https%3A%2F%2Fstellcodex.test%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback" in location
        assert settings.auth_google_state_cookie_name in set_cookie
    finally:
        settings.google_client_id = previous_client_id
        settings.google_client_secret = previous_client_secret
        settings.google_redirect_uri = previous_redirect_uri
        settings.site_url = previous_site_url


def check_workspace_route_authorization(session_factory: sessionmaker) -> None:
    member = seed_user(session_factory, email="workspace@example.com", password="WorkspacePass123!", role="member")
    db = session_factory()
    try:
        anonymous = get_optional_principal(build_request(path="/workspace"), db=db)
        principal = get_optional_principal(build_request(cookie_token=issue_token(member), path="/workspace"), db=db)

        assert anonymous is None
        assert principal is not None
        assert principal.user_id == str(member.id)
        assert principal.role == "member"
    finally:
        db.close()


def check_admin_route_authorization(session_factory: sessionmaker) -> None:
    member = seed_user(session_factory, email="member-admin-route@example.com", password="MemberAdmin123!", role="member")
    admin = seed_user(session_factory, email="admin-admin-route@example.com", password="AdminAdmin123!", role="admin")
    db = session_factory()
    try:
        member_principal = get_optional_principal(build_request(cookie_token=issue_token(member), path="/admin"), db=db)
        admin_principal = get_optional_principal(build_request(cookie_token=issue_token(admin), path="/admin"), db=db)

        assert member_principal is not None
        assert admin_principal is not None

        try:
            require_role("admin")(member_principal)
            raise AssertionError("member should not pass admin role check")
        except HTTPException as exc:
            assert exc.status_code == 403

        approved = require_role("admin")(admin_principal)
        assert approved.role == "admin"
    finally:
        db.close()


def check_public_share_route_remains_public() -> None:
    signature = inspect.signature(resolve_share_short_alias)
    assert "principal" not in signature.parameters
    assert "token" in signature.parameters
    assert "request" in signature.parameters


def check_viewer_auth_behavior_aligned(session_factory: sessionmaker) -> None:
    member = seed_user(session_factory, email="viewer@example.com", password="ViewerPass123!", role="member")
    db = session_factory()
    try:
        anonymous = get_optional_principal(build_request(path="/files/file-1/gltf"), db=db)
        principal = get_optional_principal(build_request(cookie_token=issue_token(member), path="/files/file-1/gltf"), db=db)

        assert anonymous is None
        assert principal is not None
        assert principal.role == "member"
    finally:
        db.close()


CHECKS = [
    ("local-login-success", check_local_login_success),
    ("logout-success", check_logout_success),
    ("auth-me-role-resolution", check_auth_me_role_resolution),
    ("google-auto-registration-path", check_google_auto_registration_defaults_to_member),
    ("google-admin-whitelist-behavior", check_google_admin_whitelist_behavior),
    ("google-start-uses-env", check_google_start_uses_redirect_when_env_present),
    ("workspace-route-authorization", check_workspace_route_authorization),
    ("admin-route-authorization", check_admin_route_authorization),
    ("public-share-route-remains-public", check_public_share_route_remains_public),
    ("viewer-auth-behavior-aligned", check_viewer_auth_behavior_aligned),
]


def main() -> None:
    failures = 0
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "auth-access.sqlite3"
        session_factory, engine = build_session_factory(db_path)
        try:
            for name, check in CHECKS:
                try:
                    if "session_factory" in inspect.signature(check).parameters:
                        check(session_factory)
                    else:
                        check()
                    print(f"ok - {name}")
                except Exception as error:
                    failures += 1
                    print(f"not ok - {name}")
                    print(error)
        finally:
            Base.metadata.drop_all(bind=engine, tables=[RevokedToken.__table__, PasswordResetToken.__table__, User.__table__])
            engine.dispose()

    if failures:
        raise SystemExit(1)

    print(f"tests: {len(CHECKS)}")


if __name__ == "__main__":
    main()
