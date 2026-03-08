from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.orchestrator import ensure_session_decision
from app.models.file import UploadFile
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution


def build_core_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="runtime.echo",
            description="Echo request metadata and message for safe runtime verification.",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "additionalProperties": True,
            },
            output_schema={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "project_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            permission_scope="stellai.runtime.read",
            tenant_required=True,
            handler=handle_runtime_echo,
            category="core",
            tags=("safe", "diagnostic"),
        ),
        ToolDefinition(
            name="upload.status",
            description="Read upload status for a tenant-owned file.",
            input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "status": {"type": "string"},
                    "original_filename": {"type": "string"},
                    "updated_at": {"type": ["string", "null"]},
                },
            },
            permission_scope="stellai.upload.read",
            tenant_required=True,
            handler=handle_upload_status,
            category="core",
            tags=("tenant", "db"),
        ),
        ToolDefinition(
            name="upload.decision",
            description="Read approval/decision payload for a tenant-owned file.",
            input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "state": {"type": "string"},
                    "approval_required": {"type": "boolean"},
                    "risk_flags": {"type": "array"},
                },
            },
            permission_scope="stellai.upload.read",
            tenant_required=True,
            handler=handle_upload_decision,
            category="core",
            tags=("tenant", "db"),
        ),
        ToolDefinition(
            name="orchestrator.recompute",
            description="Recompute orchestrator decision for a tenant-owned file using deterministic core.",
            input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "state": {"type": "string"},
                    "approval_required": {"type": "boolean"},
                },
            },
            permission_scope="stellai.orchestrator.execute",
            tenant_required=True,
            handler=handle_orchestrator_recompute,
            category="core",
            tags=("tenant", "orchestrator"),
        ),
    ]


def _resolve_file_id(context: RuntimeContext, params: dict[str, Any]) -> str | None:
    explicit = str(params.get("file_id") or "").strip()
    if explicit:
        return explicit
    if context.file_ids:
        return context.file_ids[0]
    return None


def _load_upload(db: Session | None, file_id: str) -> UploadFile | None:
    if db is None:
        return None
    return db.query(UploadFile).filter(UploadFile.file_id == file_id).first()


def _validate_tenant(context: RuntimeContext, row: UploadFile) -> bool:
    return str(row.tenant_id) == str(context.tenant_id)


def handle_runtime_echo(context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
    return ToolExecution(
        tool_name="runtime.echo",
        status="ok",
        output={
            "tenant_id": context.tenant_id,
            "project_id": context.project_id,
            "session_id": context.session_id,
            "message": str(params.get("message") or ""),
        },
    )


def handle_upload_status(context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
    file_id = _resolve_file_id(context, params)
    if not file_id:
        return ToolExecution(
            tool_name="upload.status",
            status="denied",
            reason="missing_file_id",
            output={"error": {"reason": "missing_file_id"}},
        )
    row = _load_upload(db, file_id)
    if row is None:
        return ToolExecution(
            tool_name="upload.status",
            status="failed",
            reason="file_not_found",
            output={"error": {"reason": "file_not_found", "file_id": file_id}},
        )
    if not _validate_tenant(context, row):
        return ToolExecution(
            tool_name="upload.status",
            status="denied",
            reason="tenant_mismatch",
            output={"error": {"reason": "tenant_mismatch", "file_id": file_id}},
        )
    return ToolExecution(
        tool_name="upload.status",
        status="ok",
        output={
            "file_id": row.file_id,
            "status": str(row.status),
            "original_filename": row.original_filename,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        },
    )


def handle_upload_decision(context: RuntimeContext, db: Session | None, params: dict[str, Any]) -> ToolExecution:
    file_id = _resolve_file_id(context, params)
    if not file_id:
        return ToolExecution(
            tool_name="upload.decision",
            status="denied",
            reason="missing_file_id",
            output={"error": {"reason": "missing_file_id"}},
        )
    row = _load_upload(db, file_id)
    if row is None:
        return ToolExecution(
            tool_name="upload.decision",
            status="failed",
            reason="file_not_found",
            output={"error": {"reason": "file_not_found", "file_id": file_id}},
        )
    if not _validate_tenant(context, row):
        return ToolExecution(
            tool_name="upload.decision",
            status="denied",
            reason="tenant_mismatch",
            output={"error": {"reason": "tenant_mismatch", "file_id": file_id}},
        )
    decision = row.decision_json if isinstance(row.decision_json, dict) else {}
    return ToolExecution(
        tool_name="upload.decision",
        status="ok",
        output={
            "file_id": row.file_id,
            "state": str(decision.get("state") or decision.get("state_code") or ""),
            "approval_required": bool(decision.get("approval_required")),
            "risk_flags": decision.get("risk_flags") if isinstance(decision.get("risk_flags"), list) else [],
            "decision_json": decision,
        },
    )


def handle_orchestrator_recompute(
    context: RuntimeContext,
    db: Session | None,
    params: dict[str, Any],
) -> ToolExecution:
    file_id = _resolve_file_id(context, params)
    if db is None:
        return ToolExecution(
            tool_name="orchestrator.recompute",
            status="failed",
            reason="db_unavailable",
            output={"error": {"reason": "db_unavailable"}},
        )
    if not file_id:
        return ToolExecution(
            tool_name="orchestrator.recompute",
            status="denied",
            reason="missing_file_id",
            output={"error": {"reason": "missing_file_id"}},
        )
    row = _load_upload(db, file_id)
    if row is None:
        return ToolExecution(
            tool_name="orchestrator.recompute",
            status="failed",
            reason="file_not_found",
            output={"error": {"reason": "file_not_found", "file_id": file_id}},
        )
    if not _validate_tenant(context, row):
        return ToolExecution(
            tool_name="orchestrator.recompute",
            status="denied",
            reason="tenant_mismatch",
            output={"error": {"reason": "tenant_mismatch", "file_id": file_id}},
        )

    session, decision = ensure_session_decision(db, row)
    return ToolExecution(
        tool_name="orchestrator.recompute",
        status="ok",
        output={
            "file_id": row.file_id,
            "session_id": str(session.id),
            "state": str(decision.get("state") or ""),
            "approval_required": bool(decision.get("approval_required")),
        },
    )
