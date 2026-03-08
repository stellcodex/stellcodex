from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.event_bus import default_event_bus
from app.core.memory_foundation import write_memory_payload
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
    try:
        db.flush()
    except Exception:
        pass
    try:
        payload = data if isinstance(data, dict) else {}
        tenant_id = str(payload.get("tenant_id") or "0")
        project_id = str(payload.get("project_id") or "default")
        try:
            default_event_bus().publish_event(
                event_type="audit.logged",
                source="service.audit",
                subject=str(file_id or event_type),
                tenant_id=tenant_id,
                project_id=project_id,
                data={
                    "audit_id": str(getattr(evt, "id", "") or ""),
                    "event_type": str(event_type),
                    "actor_user_id": str(actor_user_id or ""),
                    "actor_anon_sub": str(actor_anon_sub or ""),
                    "file_id": str(file_id or ""),
                    "timestamp": evt.created_at.isoformat() if getattr(evt, "created_at", None) else "",
                },
            )
        except Exception:
            pass
        write_memory_payload(
            record_type="audit_event",
            title=f"Audit event {event_type}",
            source_uri=f"scx://audit/{event_type}",
            tenant_id=tenant_id,
            project_id=project_id,
            tags=["phase2", "audit", str(event_type).replace(".", "_")],
            text=json.dumps(
                {
                    "event_type": event_type,
                    "actor_user_id": actor_user_id,
                    "actor_anon_sub": actor_anon_sub,
                    "file_id": file_id,
                    "data": payload,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            metadata={
                "event_type": event_type,
                "file_id": file_id,
                "actor_user_id": actor_user_id,
                "actor_anon_sub": actor_anon_sub,
            },
        )
    except Exception:
        pass
