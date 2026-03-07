from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def log_event(
    db: Session,
    event_type: str,
    actor_user_id: str | None = None,
    actor_anon_sub: str | None = None,
    file_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    evt = AuditEvent(
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_anon_sub=actor_anon_sub,
        file_id=file_id,
        data=data or {},
    )
    db.add(evt)
