from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from sqlalchemy.orm import Session

from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext


@dataclass(frozen=True)
class ToolAuditRecord:
    at: str
    tenant_id: str
    project_id: str
    session_id: str
    trace_id: str
    principal_type: str
    principal_id: str
    tool_name: str
    category: str
    permission_scope: str
    status: str
    reason: str | None
    params: dict[str, Any]
    output: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "at": self.at,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "principal_type": self.principal_type,
            "principal_id": self.principal_id,
            "tool_name": self.tool_name,
            "category": self.category,
            "permission_scope": self.permission_scope,
            "status": self.status,
            "reason": self.reason,
            "params": self.params,
            "output": self.output,
        }


class ToolAuditLogger:
    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("STELLAI_TOOL_AUDIT_PATH") or "/root/workspace/evidence/stellai/tool_invocations.jsonl"
        self.path = Path(configured).resolve()
        self._lock = Lock()

    def log_tool_result(
        self,
        *,
        context: RuntimeContext,
        definition: ToolDefinition,
        db: Session | None,
        status: str,
        reason: str | None,
        params: dict[str, Any],
        output: dict[str, Any],
    ) -> ToolAuditRecord:
        record = ToolAuditRecord(
            at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tenant_id=str(context.tenant_id),
            project_id=str(context.project_id),
            session_id=str(context.session_id),
            trace_id=str(context.trace_id),
            principal_type=str(context.principal_type),
            principal_id=str(context.principal_id),
            tool_name=definition.name,
            category=definition.category,
            permission_scope=definition.permission_scope,
            status=str(status),
            reason=reason,
            params=_sanitize_payload(params),
            output=_sanitize_payload(output),
        )
        self._append_jsonl(record.to_dict())
        self._log_db_event(context=context, definition=definition, db=db, record=record)
        return record

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def _log_db_event(
        self,
        *,
        context: RuntimeContext,
        definition: ToolDefinition,
        db: Session | None,
        record: ToolAuditRecord,
    ) -> None:
        if db is None:
            return
        try:
            from app.services.audit import log_event

            event_type = f"stellai.tool.{record.status}"
            log_event(
                db,
                event_type,
                actor_anon_sub=context.principal_id,
                file_id=str(record.params.get("file_id") or "") or None,
                data={
                    "tenant_id": context.tenant_id,
                    "project_id": context.project_id,
                    "trace_id": context.trace_id,
                    "tool_name": definition.name,
                    "category": definition.category,
                    "permission_scope": definition.permission_scope,
                    "status": record.status,
                    "reason": record.reason,
                },
            )
        except Exception:
            return



def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in (payload or {}).items():
        safe_key = str(key)
        if "token" in safe_key.lower() or "secret" in safe_key.lower() or "password" in safe_key.lower():
            sanitized[safe_key] = "***"
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str) and len(value) > 2000:
                sanitized[safe_key] = value[:2000]
            else:
                sanitized[safe_key] = value
            continue
        if isinstance(value, list):
            sanitized[safe_key] = value[:40]
            continue
        if isinstance(value, dict):
            sanitized[safe_key] = _sanitize_payload(value)
            continue
        sanitized[safe_key] = str(value)
    return sanitized
