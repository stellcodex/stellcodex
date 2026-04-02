from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal
from app.services.stell_ai_client import proxy_stell_ai
from app.services.tenants import ensure_owner_tenant_id

router = APIRouter(prefix="/stell-ai", tags=["stell-ai"])


class KnowledgeSearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=240)
    max_results: int = Field(default=5, ge=1, le=10)
    file_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)


class KnowledgeIngestIn(BaseModel):
    file_id: str | None = Field(default=None, max_length=64)
    force: bool = False
    limit_files: int | None = Field(default=None, ge=1, le=5000)


class AgentRunIn(BaseModel):
    agent_id: str = Field(min_length=2, max_length=64)
    file_id: str | None = None
    prompt: str | None = Field(default=None, max_length=2000)
    include_web_context: bool = False
    web_query: str | None = Field(default=None, max_length=240)


class AgentTaskIn(BaseModel):
    agent_id: str = Field(min_length=2, max_length=64)
    file_id: str | None = None
    prompt: str | None = Field(default=None, max_length=2000)


class AgentOrchestrateIn(BaseModel):
    tasks: list[AgentTaskIn] = Field(default_factory=list, min_length=1, max_length=8)
    include_web_context: bool = False
    web_query: str | None = Field(default=None, max_length=240)


class PluginRegisterIn(BaseModel):
    plugin_id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(min_length=2, max_length=120)
    plugin_type: str = Field(min_length=2, max_length=48)
    description: str = Field(min_length=2, max_length=500)
    entrypoint: str = Field(min_length=2, max_length=240)


class PlanIn(BaseModel):
    prompt: str = Field(min_length=2, max_length=2000)
    file_id: str | None = None


class AnalyzeIn(BaseModel):
    file_id: str = Field(min_length=4, max_length=64)
    include_web_context: bool = False
    web_query: str | None = Field(default=None, max_length=240)


class DecideIn(BaseModel):
    file_id: str | None = Field(default=None, max_length=64)
    project_id: str | None = Field(default=None, max_length=128)
    mode: str | None = Field(default=None, max_length=48)
    rule_version: str | None = Field(default=None, max_length=48)
    geometry_meta: dict[str, Any] | None = None
    dfm_findings: dict[str, Any] | None = None


class MemoryWriteIn(BaseModel):
    task_query: str = Field(min_length=2, max_length=500)
    successful_plan: dict[str, Any] = Field(default_factory=dict)
    lessons_learned: str | None = Field(default=None, max_length=4000)
    feedback_from_owner: str | None = Field(default=None, max_length=4000)


class MemorySearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=240)
    limit: int = Field(default=5, ge=1, le=20)


class ChatToolIn(BaseModel):
    tool_name: str = Field(min_length=2, max_length=128)
    permission_scope: str = Field(min_length=2, max_length=64)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatIn(BaseModel):
    session_id: str | None = Field(default=None, max_length=64)
    file_id: str | None = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=8000)
    user_tier: str = Field(default="standard", max_length=32)
    allow_tools: bool = False
    requested_tools: list[ChatToolIn] = Field(default_factory=list, max_length=8)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecuteIn(BaseModel):
    session_id: str | None = Field(default=None, max_length=64)
    tool_name: str = Field(min_length=2, max_length=128)
    permission_scope: str = Field(min_length=2, max_length=64)
    arguments: dict[str, Any] = Field(default_factory=dict)


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _get_file_by_identifier(db: Session, value: str) -> UploadFileModel | None:
    uid = _normalize_file_uuid(value)
    canonical = format_scx_file_id(uid)
    legacy = str(uid)
    return db.query(UploadFileModel).filter(UploadFileModel.file_id.in_((canonical, legacy))).first()


def _assert_file_access(file_row: UploadFileModel, principal: Principal) -> None:
    if str(file_row.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _validate_file_access(file_id: str, db: Session, principal: Principal) -> UploadFileModel:
    row = _get_file_by_identifier(db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(row, principal)
    return row


def _tenant_id_for_principal(db: Session, principal: Principal, file_row: UploadFileModel | None = None) -> int:
    if file_row is not None:
        return int(file_row.tenant_id)
    tenant_id = ensure_owner_tenant_id(db, str(principal.user_id or "anonymous"))
    db.commit()
    return tenant_id


def _tenant_payload(
    db: Session,
    principal: Principal,
    *,
    file_row: UploadFileModel | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scoped_payload = dict(payload or {})
    scoped_payload["tenant_id"] = _tenant_id_for_principal(db, principal, file_row)
    if file_row is not None:
        scoped_payload["file_id"] = file_row.file_id
    return scoped_payload


@router.get("/capabilities")
def capabilities(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return proxy_stell_ai(path="/capabilities")


@router.get("/agents")
def list_agents(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return proxy_stell_ai(path="/agents")


@router.post("/knowledge/search")
def knowledge_search(
    data: KnowledgeSearchIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = {
        "tenant_id": _tenant_id_for_principal(db, principal, row),
        "query": data.query,
        "max_results": data.max_results,
        "session_id": data.session_id,
    }
    if row is not None:
        payload["file_id"] = row.file_id
    return proxy_stell_ai(path="/knowledge/search", method="POST", payload=payload)


@router.post("/knowledge/ingest")
def knowledge_ingest(
    data: KnowledgeIngestIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    return proxy_stell_ai(
        path="/knowledge/ingest",
        method="POST",
        payload=_tenant_payload(
            db,
            principal,
            file_row=row,
            payload={
                "force": data.force,
                "limit_files": data.limit_files,
            },
        ),
        timeout=180,
    )


@router.post("/knowledge/query")
def knowledge_query(
    data: KnowledgeSearchIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = {
        "tenant_id": _tenant_id_for_principal(db, principal, row),
        "query": data.query,
        "max_results": data.max_results,
        "session_id": data.session_id,
    }
    if row is not None:
        payload["file_id"] = row.file_id
    return proxy_stell_ai(path="/knowledge/query", method="POST", payload=payload)


@router.get("/analysis/{file_id}")
def file_analysis(
    file_id: str,
    include_web_context: bool = False,
    web_query: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(file_id, db, principal)
    return proxy_stell_ai(
        path=f"/analysis/{row.file_id}",
        query={"include_web_context": include_web_context, "web_query": web_query},
    )


@router.post("/agents/run")
def run_agent(
    data: AgentRunIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = _tenant_payload(db, principal, file_row=row, payload=data.model_dump())
    return proxy_stell_ai(path="/agents/run", method="POST", payload=payload)


@router.post("/agents/orchestrate")
def orchestrate_agents(
    data: AgentOrchestrateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    tasks: list[dict[str, Any]] = []
    for task in data.tasks:
        if task.file_id:
            row = _validate_file_access(task.file_id, db, principal)
            tasks.append({**task.model_dump(), "file_id": row.file_id})
        else:
            tasks.append(task.model_dump())
    return proxy_stell_ai(
        path="/agents/orchestrate",
        method="POST",
        payload=_tenant_payload(
            db,
            principal,
            payload={
                "tasks": tasks,
                "include_web_context": data.include_web_context,
                "web_query": data.web_query,
            },
        ),
    )


@router.get("/plugins")
def list_plugins(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return proxy_stell_ai(path="/plugins")


@router.post("/plugins/register", status_code=201)
def register_plugin(data: PluginRegisterIn, principal: Principal = Depends(get_current_principal)):
    _ = principal
    return proxy_stell_ai(path="/plugins/register", method="POST", payload=data.model_dump())


@router.post("/plan")
def plan(
    data: PlanIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _ = principal
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = _tenant_payload(db, principal, file_row=row, payload=data.model_dump())
    return proxy_stell_ai(path="/plan", method="POST", payload=payload)


@router.post("/analyze")
def analyze(
    data: AnalyzeIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal)
    return proxy_stell_ai(
        path="/analyze",
        method="POST",
        payload=_tenant_payload(db, principal, file_row=row, payload=data.model_dump()),
    )


@router.post("/decide")
def decide(
    data: DecideIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _ = principal
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = _tenant_payload(db, principal, file_row=row, payload=data.model_dump())
    return proxy_stell_ai(path="/decide", method="POST", payload=payload)


@router.post("/memory/write")
def memory_write(
    data: MemoryWriteIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return proxy_stell_ai(
        path="/memory/write",
        method="POST",
        payload=_tenant_payload(db, principal, payload=data.model_dump()),
    )


@router.post("/memory/search")
def memory_search(
    data: MemorySearchIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return proxy_stell_ai(
        path="/memory/search",
        method="POST",
        payload=_tenant_payload(db, principal, payload=data.model_dump()),
    )


@router.post("/chat")
def chat(
    data: ChatIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _validate_file_access(data.file_id, db, principal) if data.file_id else None
    payload = _tenant_payload(db, principal, file_row=row, payload=data.model_dump())
    return proxy_stell_ai(path="/chat", method="POST", payload=payload, timeout=60)


@router.get("/chat/{session_id}")
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return proxy_stell_ai(
        path=f"/chat/{session_id}",
        query={"tenant_id": _tenant_id_for_principal(db, principal)},
        timeout=30,
    )


@router.get("/tools")
def tools(principal: Principal = Depends(get_current_principal)):
    _ = principal
    return proxy_stell_ai(path="/tools")


@router.post("/tools/execute")
def tools_execute(
    data: ToolExecuteIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    arguments = data.arguments if isinstance(data.arguments, dict) else {}
    row = None
    if isinstance(arguments.get("file_id"), str) and arguments.get("file_id"):
        row = _validate_file_access(str(arguments["file_id"]), db, principal)
        arguments = {**arguments, "file_id": row.file_id}
    return proxy_stell_ai(
        path="/tools/execute",
        method="POST",
        payload={
            "tenant_id": _tenant_id_for_principal(db, principal, row),
            "session_id": data.session_id,
            "tool_name": data.tool_name,
            "permission_scope": data.permission_scope,
            "arguments": arguments,
        },
        timeout=60,
    )
