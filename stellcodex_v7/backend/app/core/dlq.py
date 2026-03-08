from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.event_bus import EventBus
from app.core.event_types import EventType, FAILURE_CODES
from app.core.events import EventEnvelope
from app.models.phase2 import DlqRecord
from app.services.audit import log_event


@dataclass
class StageExecutionError(Exception):
    message: str
    failure_code: str = "UNKNOWN"
    transient: bool = False

    def __str__(self) -> str:
        return self.message


class TransientStageError(StageExecutionError):
    def __init__(self, message: str, failure_code: str = "UNKNOWN") -> None:
        super().__init__(message=message, failure_code=failure_code, transient=True)


class PermanentStageError(StageExecutionError):
    def __init__(self, message: str, failure_code: str = "UNKNOWN") -> None:
        super().__init__(message=message, failure_code=failure_code, transient=False)


def _normalize_failure_code(code: str | None) -> str:
    token = str(code or "UNKNOWN").strip().upper()
    return token if token in FAILURE_CODES else "UNKNOWN"


def record_dead_letter(
    db: Session,
    bus: EventBus,
    *,
    envelope: EventEnvelope,
    stage: str,
    failure_code: str,
    error_detail: str,
    retry_count: int,
    payload_json: dict[str, Any] | None = None,
) -> DlqRecord:
    code = _normalize_failure_code(failure_code)
    record = DlqRecord(
        id=uuid4(),
        event_id=envelope.id,
        event_type=envelope.type,
        file_id=str(envelope.data.get("file_id") or ""),
        version_no=int(envelope.data.get("version_no") or 1),
        stage=stage,
        failure_code=code,
        error_detail=error_detail[:4000],
        retry_count=max(0, int(retry_count)),
        payload_json=payload_json if isinstance(payload_json, dict) else envelope.to_dict(),
    )
    db.add(record)

    # Keep existing audit trail and add stream event for downstream observers.
    log_event(
        db,
        EventType.JOB_FAILED.value,
        file_id=record.file_id or None,
        data={
            "event_id": envelope.id,
            "stage": stage,
            "failure_code": code,
            "retry_count": record.retry_count,
            "error": error_detail[:300],
        },
    )

    bus.publish_event(
        event_type=EventType.JOB_FAILED.value,
        source="worker.dlq",
        subject=record.file_id or envelope.subject,
        tenant_id=str(envelope.tenant_id or "0"),
        project_id=str(envelope.project_id or "default"),
        trace_id=envelope.trace_id,
        data={
            "file_id": record.file_id,
            "version_no": record.version_no,
            "stage": stage,
            "failure_code": code,
            "error": error_detail[:500],
            "retry_count": record.retry_count,
            "event_id": envelope.id,
        },
    )
    db.commit()
    return record
