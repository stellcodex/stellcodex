from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id
from app.db.session import get_db
from app.models.file import UploadFile
from app.security.deps import Principal, get_current_principal
from app.services.tenant_identity import resolve_or_create_tenant_id
from app.stellai.service import get_stellai_runtime
from app.stellai.tools import GLOBAL_ALLOWLIST
from app.stellai.types import RuntimeContext, RuntimeRequest

router = APIRouter(prefix="/stell-ai", tags=["stell-ai"])


class ToolRequestIn(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class RuntimeExecuteIn(BaseModel):
    message: str
    session_id: str | None = None
    trace_id: str | None = None
    project_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    # Client-provided tool permission grants are ignored; permissions are server-derived.
    allowed_tools: list[str] = Field(default_factory=list)
    tool_requests: list[ToolRequestIn] = Field(default_factory=list)
    top_k: int = 6


class RuntimeExecuteOut(BaseModel):
    session_id: str
    trace_id: str
    reply: str
    plan: dict[str, Any]
    retrieval: dict[str, Any]
    tool_results: list[dict[str, Any]]
    memory: dict[str, Any]
    evaluation: dict[str, Any]
    events: list[dict[str, Any]]


def _assert_file_access(row: UploadFile, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if row.owner_anon_sub != owner_sub and row.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if principal.typ != "user":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if str(row.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _normalize_file_id(value: str) -> str:
    try:
        return format_scx_file_id(normalize_scx_file_id(value))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid file id: {value}") from exc


def _resolve_runtime_scope(
    *,
    db: Session,
    principal: Principal,
    requested_file_ids: list[str],
    requested_project_id: str | None,
) -> tuple[str, str, tuple[str, ...]]:
    normalized_ids = tuple(_normalize_file_id(item) for item in requested_file_ids)
    if normalized_ids:
        rows = db.query(UploadFile).filter(UploadFile.file_id.in_(normalized_ids)).all()
        found = {row.file_id: row for row in rows}
        missing = [file_id for file_id in normalized_ids if file_id not in found]
        if missing:
            raise HTTPException(status_code=404, detail=f"Files not found: {missing}")
        for row in found.values():
            _assert_file_access(row, principal)
        tenant_ids = {str(row.tenant_id) for row in found.values()}
        if len(tenant_ids) != 1:
            raise HTTPException(status_code=400, detail="All file_ids must belong to the same tenant")
        tenant_id = sorted(tenant_ids)[0]
        if requested_project_id:
            project_id = requested_project_id
        else:
            sample_meta = next(iter(found.values())).meta
            if isinstance(sample_meta, dict):
                project_id = str(sample_meta.get("project_id") or "default")
            else:
                project_id = "default"
        return tenant_id, project_id, normalized_ids

    if principal.typ == "guest":
        tenant_id = str(resolve_or_create_tenant_id(db, principal.owner_sub or "anonymous"))
    elif principal.typ == "user":
        row = (
            db.query(UploadFile)
            .filter(UploadFile.owner_user_id == principal.user_id)
            .order_by(UploadFile.updated_at.desc())
            .first()
        )
        if row is not None:
            tenant_id = str(row.tenant_id)
        else:
            tenant_id = str(resolve_or_create_tenant_id(db, f"user:{principal.user_id}"))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return tenant_id, str(requested_project_id or "default"), ()


_PRIVILEGED_ROLES: frozenset[str] = frozenset({"admin", "owner", "founder", "service"})
_STANDARD_USER_ROLES: frozenset[str] = frozenset({"user", "member", "engineer", "operator", "analyst"})
_STANDARD_USER_TOOLS: frozenset[str] = frozenset(
    {
        "runtime.echo",
        "upload.status",
        "upload.decision",
        "orchestrator.recompute",
        "system_info",
        "runtime_status",
        "process_status",
        "disk_usage",
        "read_file",
        "list_directory",
        "search_files",
        "csv_reader",
        "data_summary",
        "data_filter",
        "json_transform",
        "mesh_info",
        "mesh_volume",
        "mesh_surface_area",
        "mesh_bounds",
        "doc_search",
        "repo_search",
        "knowledge_lookup",
        "text_summary",
    }
)
_GUEST_TOOLS: frozenset[str] = frozenset(
    {
        "runtime.echo",
        "upload.status",
        "upload.decision",
        "doc_search",
        "repo_search",
        "knowledge_lookup",
        "text_summary",
    }
)
_LEAST_PRIVILEGE_TOOLS: frozenset[str] = frozenset({"runtime.echo"})


def _resolve_server_allowed_tools(
    *,
    principal: Principal,
    tenant_id: str,
    project_id: str,
    file_ids: tuple[str, ...],
) -> frozenset[str]:
    _ = (tenant_id, project_id, file_ids)
    if principal.typ == "guest":
        return _GUEST_TOOLS
    if principal.typ == "user":
        role = str(principal.role or "").strip().lower()
        if role in _PRIVILEGED_ROLES:
            return GLOBAL_ALLOWLIST
        if role in _STANDARD_USER_ROLES:
            return _STANDARD_USER_TOOLS
    return _LEAST_PRIVILEGE_TOOLS


@router.post("/runtime/execute", response_model=RuntimeExecuteOut)
def execute_stell_ai_runtime(
    body: RuntimeExecuteIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    tenant_id, project_id, normalized_file_ids = _resolve_runtime_scope(
        db=db,
        principal=principal,
        requested_file_ids=body.file_ids,
        requested_project_id=body.project_id,
    )

    effective_allowed_tools = _resolve_server_allowed_tools(
        principal=principal,
        tenant_id=tenant_id,
        project_id=project_id,
        file_ids=normalized_file_ids,
    )

    context = RuntimeContext(
        tenant_id=tenant_id,
        project_id=project_id,
        principal_type=principal.typ,
        principal_id=str(principal.user_id or principal.owner_sub or "anonymous"),
        session_id=body.session_id or f"sess_{uuid4().hex[:16]}",
        trace_id=body.trace_id or str(uuid4()),
        file_ids=normalized_file_ids,
        allowed_tools=effective_allowed_tools,
    )
    request = RuntimeRequest(
        message=message,
        context=context,
        top_k=max(1, min(int(body.top_k or 6), 20)),
        tool_requests=[item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in body.tool_requests],
        metadata_filters={"project_id": project_id},
    )
    runtime = get_stellai_runtime()
    result = runtime.run(request=request, db=db)
    payload = result.to_dict()
    return RuntimeExecuteOut(**payload)
