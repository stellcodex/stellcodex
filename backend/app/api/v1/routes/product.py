import os
from pathlib import Path
from typing import Optional
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, File as FastFile, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.config import settings
from app.core.ids import normalize_scx_id
from app.core.render_presets import get_render_preset
from app.core.storage import get_s3_client, get_s3_presign_client
from app.api.v1.routes.files import FileOut, direct_upload
from app.models.core import File, FileKind, Job, JobStatus, JobType, Project, Revision
from app.models.file import UploadFile as UploadFileModel
from app.queue import get_queue
from app.schemas import StatusResponse
from app.security.deps import Principal, get_current_principal
from app.security.jwt import decode_token
from app.storage import Storage, storage_key_for_2d, storage_key_for_3d
from app.utils import revision_label
from app.workers.cad_worker import process_cad_lod0
from app.workers.drawing_worker import process_drawing
from app.workers.render_worker import process_render

router = APIRouter(tags=["product"])


class RenderRequest(BaseModel):
    revision_id: UUID
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
    return await direct_upload(upload=selected, db=db, principal=principal)


@router.get("/status/{revision_id}", response_model=StatusResponse)
def status(revision_id: str, db: Session = Depends(get_db)):
    revision_uuid = _revision_uuid_from_identifier(revision_id)
    revision = db.get(Revision, revision_uuid)
    if revision is None:
        raise HTTPException(status_code=404, detail="revision not found")

    s3 = get_s3_presign_client(settings) if settings.s3_enabled else None

    jobs = revision.jobs
    artifacts = revision.artifacts

    return StatusResponse(
        file_id=normalize_scx_id(str(revision.id)),
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
                "url": (
                    s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": settings.s3_bucket, "Key": a.storage_key},
                        ExpiresIn=900,
                    )
                    if s3
                    else None
                ),
                "glb_url": (
                    s3.generate_presigned_url(
                        "head_object",
                        Params={"Bucket": settings.s3_bucket, "Key": a.storage_key},
                        ExpiresIn=900,
                    )
                    if (s3 and a.type.value == "lod0_glb")
                    else None
                ),
            }
            for a in artifacts
        ],
    )

@router.post("/render", response_model=RenderResponse)
def render(request: RenderRequest, db: Session = Depends(get_db)):
    preset = get_render_preset(request.preset)
    revision = db.get(Revision, request.revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail="revision not found")

    job = Job(revision_id=revision.id, type=JobType.RENDER, status=JobStatus.QUEUED, queue="render")
    db.add(job)
    db.commit()
    db.refresh(job)

    q = get_queue("render")
    q.enqueue(process_render, str(job.id), preset.name, job_id=str(job.id))

    return RenderResponse(job_id=job.id, preset=preset.name)
