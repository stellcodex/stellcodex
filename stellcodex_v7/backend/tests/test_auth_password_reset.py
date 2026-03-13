from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.routes import users as users_routes
from app.models.user import PasswordResetToken, User


class FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter_by(self, **kwargs):
        rows = []
        for row in self._rows:
            if all(getattr(row, key) == value for key, value in kwargs.items()):
                rows.append(row)
        return FakeQuery(rows)

    def first(self):
        return self._rows[0] if self._rows else None


class FakeDB:
    def __init__(self) -> None:
        self.users: dict = {}
        self.reset_tokens: dict = {}
        self.commit_count = 0

    def add(self, row) -> None:
        if isinstance(row, User):
            self.users[row.id] = row
        elif isinstance(row, PasswordResetToken):
            self.reset_tokens[row.id] = row
        else:
            raise TypeError(type(row))

    def commit(self) -> None:
        self.commit_count += 1

    def get(self, model, key):
        if model is User:
            return self.users.get(key)
        if model is PasswordResetToken:
            return self.reset_tokens.get(key)
        raise TypeError(model)

    def query(self, model):
        if model is User:
            return FakeQuery(self.users.values())
        if model is PasswordResetToken:
            return FakeQuery(self.reset_tokens.values())
        raise TypeError(model)


def _make_user(email: str = "user@example.com") -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash=users_routes._hash_password("old-secret"),
        role="user",
        is_suspended=False,
    )


def test_request_password_reset_creates_token_and_sends_mail(monkeypatch) -> None:
    db = FakeDB()
    user = _make_user()
    db.add(user)
    captured: dict[str, str] = {}

    monkeypatch.setattr(users_routes, "email_delivery_enabled", lambda: True)

    def _fake_send(email: str, token: str) -> bool:
        captured["email"] = email
        captured["token"] = token
        return True

    monkeypatch.setattr(users_routes, "send_password_reset", _fake_send)

    result = users_routes.request_password_reset(users_routes.PasswordResetRequestIn(email=user.email), db)

    assert result.ok is True
    assert result.delivery_enabled is True
    assert captured["email"] == user.email
    assert len(db.reset_tokens) == 1
    stored = next(iter(db.reset_tokens.values()))
    assert stored.user_id == user.id
    assert stored.token_hash == users_routes._hash_reset_token(captured["token"])


def test_request_password_reset_hides_missing_user(monkeypatch) -> None:
    db = FakeDB()
    monkeypatch.setattr(users_routes, "email_delivery_enabled", lambda: True)
    monkeypatch.setattr(users_routes, "send_password_reset", lambda email, token: True)

    result = users_routes.request_password_reset(
        users_routes.PasswordResetRequestIn(email="missing@example.com"),
        db,
    )

    assert result.ok is True
    assert result.delivery_enabled is True
    assert db.reset_tokens == {}


def test_request_password_reset_reports_disabled_delivery(monkeypatch) -> None:
    db = FakeDB()
    db.add(_make_user())
    monkeypatch.setattr(users_routes, "email_delivery_enabled", lambda: False)
    monkeypatch.setattr(users_routes, "send_password_reset", lambda email, token: True)

    result = users_routes.request_password_reset(
        users_routes.PasswordResetRequestIn(email="user@example.com"),
        db,
    )

    assert result.ok is True
    assert result.delivery_enabled is False
    assert db.reset_tokens == {}


def test_reset_password_updates_hash_and_marks_token_used() -> None:
    db = FakeDB()
    user = _make_user()
    db.add(user)
    raw_token = "reset-token-123"
    token_row = PasswordResetToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=users_routes._hash_reset_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        used_at=None,
    )
    db.add(token_row)

    result = users_routes.reset_password(
        users_routes.PasswordResetIn(token=raw_token, password="new-secret"),
        db,
    )

    assert result.ok is True
    assert users_routes._verify_password("new-secret", user.password_hash)
    assert token_row.used_at is not None


def test_reset_password_rejects_invalid_or_expired_token() -> None:
    db = FakeDB()
    user = _make_user()
    db.add(user)
    token_row = PasswordResetToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=users_routes._hash_reset_token("expired-token"),
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        used_at=None,
    )
    db.add(token_row)

    with pytest.raises(HTTPException) as exc_info:
        users_routes.reset_password(
            users_routes.PasswordResetIn(token="expired-token", password="new-secret"),
            db,
        )

    assert exc_info.value.status_code == 400
    assert "invalid or expired" in str(exc_info.value.detail).lower()
