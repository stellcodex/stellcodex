from __future__ import annotations

from typing import Optional
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, File as FastFile, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.core.render_presets import get_render_preset
from app.api.v1.routes.files import FileOut, direct_upload
from app.models.core import File, FileKind, Job, JobStatus, JobType, Project, Revision
from app.models.file import UploadFile as UploadFileModel
from app.queue import get_queue
from app.schemas import StatusResponse
from app.security.deps import Principal, get_current_principal
from app.security.jwt import decode_token
from app.workers.render_worker import process_render

router = APIRouter(tags=["product"])


class RenderRequest(BaseModel):
    file_id: str
    preset: str


class RenderResponse(BaseModel):
    job_id: UUID
    preset: str


def _upload_owner(request: Request) -> tuple[str, str | None, str | None, bool]:
    auth = (request.headers.get("Authorization") or "").strip()
    if not auth:
        owner_sub = f"legacy-upload:{uuid4()}"
        return owner_sub, None, owner_sub, True
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    payload = decode_token(token)
    typ = payload.get("typ")
    if typ == "guest":
        owner_sub = str(payload.get("owner_sub") or "").strip()
        if not owner_sub:
            raise HTTPException(status_code=401, detail="Invalid guest token")
        return owner_sub, None, owner_sub, bool(payload.get("anon", True))
    if typ == "user":
        user_id = str(payload.get("sub") or "").strip()
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        return user_id, user_id, None, False
    raise HTTPException(status_code=401, detail="Invalid token type")


def _revision_uuid_from_identifier(value: str) -> UUID:
    raw = (value or "").strip()
    try:
        return UUID(raw)
    except ValueError:
        pass
    try:
        normalized = normalize_scx_id(raw)
        return UUID(normalized.split("_", 1)[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail="revision not found")


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


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post(
    "/upload",
    response_model=FileOut,
    deprecated=True,
    summary="Legacy upload alias (deprecated)",
    description="DEPRECATED: use /api/v1/files/upload.",
)
async def upload(
    file: UploadFile | None = FastFile(default=None),
    upload: UploadFile | None = FastFile(default=None),
    project_id: Optional[UUID] = None,
    project_name: Optional[str] = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _ = (project_id, project_name)
    selected = file or upload
    if selected is None:
        raise HTTPException(
            status_code=422,
            detail="Missing multipart file field: expected 'file' or 'upload'.",
        )
    return await direct_upload(upload=selected, project_id=None, projectId=None, db=db, principal=principal)


@router.get("/status/{file_id}", response_model=StatusResponse)
def status(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = _get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    revision_uuid = _revision_uuid_from_identifier(file_row.file_id)
    revision = db.get(Revision, revision_uuid)
    public_file_id = normalize_scx_id(str(revision_uuid))
    if revision is None:
        return StatusResponse(file_id=public_file_id, jobs=[], artifacts=[])

    jobs = revision.jobs
    artifacts = revision.artifacts

    return StatusResponse(
        file_id=public_file_id,
        jobs=[
            {
                "id": j.id,
                "type": j.type.value,
                "status": j.status.value,
                "queue": j.queue,
                "error": j.error,
                "created_at": j.created_at,
                "started_at": j.started_at,
                "finished_at": j.finished_at,
            }
            for j in jobs
        ],
        artifacts=[
            {
                "id": a.id,
                "type": a.type.value,
                "ready": a.ready,
                "content_type": a.content_type,
                "size": a.size,
                "created_at": a.created_at,
                # Public contract must never expose internal storage keys via presigned URLs.
                "url": None,
                "glb_url": None,
            }
            for a in artifacts
        ],
    )


@router.post("/render", response_model=RenderResponse)
def render(
    request: RenderRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    preset = get_render_preset(request.preset)
    file_row = _get_file_by_identifier(db, request.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    revision_uuid = _revision_uuid_from_identifier(file_row.file_id)
    revision = db.get(Revision, revision_uuid)
    if revision is None:
        raise HTTPException(status_code=404, detail="revision not found for file_id")

    job = Job(rev_uid=revision.id, type=JobType.RENDER, status=JobStatus.QUEUED, queue="render")
    db.add(job)
    db.commit()
    db.refresh(job)

    q = get_queue("render")
    q.enqueue(process_render, str(job.id), preset.name, job_id=str(job.id))

    return RenderResponse(job_id=job.id, preset=preset.name)
