from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.v1.routes import share as share_routes
from app.security.deps import Principal


def _request(path: str = "/api/v1/share/token", ip: str = "203.0.113.10") -> SimpleNamespace:
    return SimpleNamespace(
        headers={"user-agent": "unit-test", "x-forwarded-for": ip},
        url=SimpleNamespace(path=path),
        client=SimpleNamespace(host=ip),
    )


def _share(**overrides):
    payload = {
        "id": "share-1",
        "file_id": "scx_file_11111111-1111-1111-1111-111111111111",
        "token": "token-abc",
        "permission": "download",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "revoked_at": None,
        "created_by_user_id": "owner-1",
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def _file(**overrides):
    payload = {
        "file_id": "scx_file_11111111-1111-1111-1111-111111111111",
        "status": "ready",
        "owner_anon_sub": "guest-1",
        "owner_sub": "guest-1",
        "owner_user_id": "owner-1",
        "tenant_id": 42,
        "meta": {"project_id": "default"},
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


class _Query:
    def __init__(self, row):
        self._row = row

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._row

    def all(self):
        return [] if self._row is None else [self._row]


class _ShareDB:
    def __init__(self, share_row=None, file_row=None):
        self.share_row = share_row
        self.file_row = file_row
        self.commits = 0
        self.added = []

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "Share":
            return _Query(self.share_row)
        return _Query(self.file_row)

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.commits += 1

    def refresh(self, _row):
        return None


class ShareContractTests(unittest.TestCase):
    def test_resolve_active_share_returns_410_for_expired_token(self) -> None:
        db = _ShareDB(
            share_row=_share(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
            file_row=_file(),
        )

        with patch.object(share_routes, "_enforce_token_probe_rate_limit", return_value=None), \
             patch.object(share_routes, "_audit_share_event") as audit_mock:
            with self.assertRaises(HTTPException) as ctx:
                share_routes._resolve_active_share(db, "token-abc", request=_request())

        self.assertEqual(ctx.exception.status_code, 410)
        audit_mock.assert_called_once()
        self.assertEqual(audit_mock.call_args.args[1], "share.access_denied")
        self.assertEqual(audit_mock.call_args.kwargs["extra"]["reason"], "expired")

    def test_invalid_share_token_fails_safely_without_echoing_token(self) -> None:
        db = _ShareDB(share_row=None, file_row=None)

        with patch.object(share_routes, "_enforce_token_probe_rate_limit", return_value=None), \
             patch.object(share_routes, "log_event") as log_mock:
            with self.assertRaises(HTTPException) as ctx:
                share_routes._resolve_active_share(db, "bad-token-1234567890", request=_request())

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Invalid share token")
        log_mock.assert_called_once()
        self.assertNotIn("bad-token-1234567890", str(log_mock.call_args.kwargs["data"]))

    def test_resolve_active_share_returns_403_for_revoked_token_immediately(self) -> None:
        db = _ShareDB(share_row=_share(revoked_at=datetime.now(timezone.utc)), file_row=_file())

        with patch.object(share_routes, "_enforce_token_probe_rate_limit", return_value=None), \
             patch.object(share_routes, "_audit_share_event") as audit_mock:
            with self.assertRaises(HTTPException) as ctx:
                share_routes._resolve_active_share(db, "token-abc", request=_request())

        self.assertEqual(ctx.exception.status_code, 403)
        audit_mock.assert_called_once()
        self.assertEqual(audit_mock.call_args.kwargs["extra"]["reason"], "revoked")

    def test_share_rate_limit_returns_429_and_writes_audit(self) -> None:
        share = _share()
        request = _request()
        db = _ShareDB()

        class FakeRedis:
            def incr(self, _key):
                return share_routes.SHARE_RATE_LIMIT_REQUESTS + 1

            def expire(self, *_args, **_kwargs):
                return True

        with patch.object(share_routes, "redis_conn", FakeRedis()), \
             patch.object(share_routes, "log_event") as log_mock:
            with self.assertRaises(HTTPException) as ctx:
                share_routes._enforce_share_rate_limit(db, share, "token-abc", request)

        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(db.commits, 1)
        log_mock.assert_called_once()
        self.assertEqual(log_mock.call_args.args[1], "share.rate_limited")

    def test_token_probe_rate_limit_returns_429_and_writes_audit(self) -> None:
        request = _request(path="/api/v1/share/bad-token")
        db = _ShareDB()

        class FakeRedis:
            def incr(self, _key):
                return share_routes.SHARE_TOKEN_RATE_LIMIT_REQUESTS + 1

            def expire(self, *_args, **_kwargs):
                return True

        with patch.object(share_routes, "redis_conn", FakeRedis()), \
             patch.object(share_routes, "log_event") as log_mock:
            with self.assertRaises(HTTPException) as ctx:
                share_routes._enforce_token_probe_rate_limit(db, "bad-token", request)

        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(db.commits, 1)
        log_mock.assert_called_once()
        self.assertEqual(log_mock.call_args.args[1], "share.token_probe_rate_limited")

    def test_cross_tenant_share_create_is_forbidden(self) -> None:
        file_row = _file(owner_anon_sub="guest-2", owner_sub="guest-2", owner_user_id="owner-2")
        principal = Principal(typ="guest", owner_sub="guest-1", anon=True)
        payload = share_routes.ShareCreateIn(permission="download", expires_in_seconds=600)

        with patch.object(share_routes, "_get_file_by_identifier", return_value=file_row):
            with self.assertRaises(HTTPException) as ctx:
                share_routes.create_share(file_row.file_id, payload, db=_ShareDB(), principal=principal)

        self.assertEqual(ctx.exception.status_code, 403)

    def test_cross_tenant_share_revoke_is_forbidden(self) -> None:
        db = _ShareDB(share_row=_share(file_id="scx_file_22222222-2222-2222-2222-222222222222"), file_row=_file(owner_sub="guest-2", owner_anon_sub="guest-2"))
        principal = Principal(typ="guest", owner_sub="guest-1", anon=True)

        with self.assertRaises(HTTPException) as ctx:
            share_routes.revoke_share("share-1", db=db, principal=principal)

        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
