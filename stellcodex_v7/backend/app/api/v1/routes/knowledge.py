from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.event_bus import default_event_bus
from app.core.ids import format_scx_file_id, normalize_scx_file_id
from app.db.session import get_db
from app.knowledge.service import get_knowledge_service
from app.models.file import UploadFile
from app.security.deps import Principal, get_current_principal
from app.services.tenant_identity import resolve_or_create_tenant_id

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeSearchIn(BaseModel):
    query: str
    tenant_id: str | None = None
    project_id: str | None = None
    file_id: str | None = None
    top_k: int = 6
    source_types: list[str] = Field(default_factory=list)


class KnowledgeSearchResult(BaseModel):
    record_id: str
    score: float
    title: str
    text: str
    metadata: dict[str, Any]
    source_ref: str


class KnowledgeSearchOut(BaseModel):
    results: list[KnowledgeSearchResult]
    tenant_id: str
    project_id: str | None = None
    file_id: str | None = None
    count: int


class KnowledgeIndexIn(BaseModel):
    tenant_id: str | None = None
    project_id: str | None = None
    file_id: str | None = None
    source_types: list[str] = Field(default_factory=list)
    document_paths: list[str] = Field(default_factory=list)
    include_events: bool = True


class KnowledgeIndexOut(BaseModel):
    status: str
    tenant_id: str
    project_id: str | None = None
    file_id: str | None = None
    indexed: int
    skipped: int
    failed: int
    total: int
    deleted: int | None = None
    reindexed: bool | None = None


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


def _resolve_scope(
    *,
    db: Session,
    principal: Principal,
    requested_file_id: str | None,
    requested_project_id: str | None,
) -> tuple[str, str, str | None]:
    if requested_file_id:
        normalized_file_id = _normalize_file_id(requested_file_id)
        row = db.query(UploadFile).filter(UploadFile.file_id == normalized_file_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="File not found")
        _assert_file_access(row, principal)
        meta = row.meta if isinstance(row.meta, dict) else {}
        return str(row.tenant_id), str(requested_project_id or meta.get("project_id") or "default"), normalized_file_id

    if principal.typ == "guest":
        tenant_id = str(resolve_or_create_tenant_id(db, principal.owner_sub or "anonymous"))
    elif principal.typ == "user":
        latest = (
            db.query(UploadFile)
            .filter(UploadFile.owner_user_id == principal.user_id)
            .order_by(UploadFile.updated_at.desc())
            .first()
        )
        if latest is not None:
            tenant_id = str(latest.tenant_id)
        else:
            tenant_id = str(resolve_or_create_tenant_id(db, f"user:{principal.user_id}"))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return tenant_id, str(requested_project_id or "default"), None


@router.post("/search", response_model=KnowledgeSearchOut)
def search_knowledge(
    body: KnowledgeSearchIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    query = str(body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    tenant_id, project_id, file_id = _resolve_scope(
        db=db,
        principal=principal,
        requested_file_id=body.file_id,
        requested_project_id=body.project_id,
    )
    service = get_knowledge_service()
    results = service.search_knowledge(
        db=db,
        query=query,
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        top_k=max(1, min(int(body.top_k or 6), 40)),
        source_types=body.source_types,
    )
    return KnowledgeSearchOut(
        results=[KnowledgeSearchResult(**item) for item in results],
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        count=len(results),
    )


@router.post("/index", response_model=KnowledgeIndexOut)
def index_knowledge(
    body: KnowledgeIndexIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    tenant_id, project_id, file_id = _resolve_scope(
        db=db,
        principal=principal,
        requested_file_id=body.file_id,
        requested_project_id=body.project_id,
    )
    service = get_knowledge_service()
    summary = service.index_scope(
        db=db,
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        source_types=body.source_types,
        document_paths=body.document_paths,
        include_events=bool(body.include_events),
    )
    if body.document_paths:
        try:
            default_event_bus().publish_event(
                event_type="document.imported",
                source="api.knowledge.index",
                subject=file_id or project_id,
                tenant_id=tenant_id,
                project_id=project_id,
                data={"paths": list(body.document_paths), "file_id": file_id, "project_id": project_id},
            )
        except Exception:
            pass
    db.commit()
    return KnowledgeIndexOut(**summary)


@router.post("/reindex", response_model=KnowledgeIndexOut)
def reindex_knowledge(
    body: KnowledgeIndexIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    tenant_id, project_id, file_id = _resolve_scope(
        db=db,
        principal=principal,
        requested_file_id=body.file_id,
        requested_project_id=body.project_id,
    )
    service = get_knowledge_service()
    summary = service.reindex_scope(
        db=db,
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        source_types=body.source_types,
        document_paths=body.document_paths,
    )
    db.commit()
    return KnowledgeIndexOut(**summary)


@router.get("/records/{record_id}")
def get_knowledge_record(
    record_id: str,
    project_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    tenant_id, project, _file_id = _resolve_scope(
        db=db,
        principal=principal,
        requested_file_id=None,
        requested_project_id=project_id,
    )
    service = get_knowledge_service()
    payload = service.get_record(db=db, record_id=record_id, tenant_id=tenant_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Knowledge record not found")
    if payload.get("project_id") and project and payload.get("project_id") != project:
        raise HTTPException(status_code=404, detail="Knowledge record not found")
    return payload


@router.get("/health")
def knowledge_health(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _ = principal
    return get_knowledge_service().health(db=db)
