import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File as FastFile, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.config import settings
from app.core.render_presets import get_render_preset
from app.core.storage import get_s3_client, get_s3_presign_client
from app.models.core import File, FileKind, Job, JobStatus, JobType, Project, Revision
from app.queue import get_queue
from app.schemas import StatusResponse, UploadResponse
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


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = FastFile(...),
    project_id: Optional[UUID] = None,
    project_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")

    ext = Path(file.filename).suffix.lower()
    is_2d = ext == ".dxf"

    if is_2d:
        kind = FileKind.SOURCE_2D
    else:
        kind = FileKind.SOURCE_3D

    if project_id is None:
        name = project_name or os.path.splitext(file.filename)[0]
        project = Project(name=name)
        db.add(project)
        db.commit()
        db.refresh(project)
    else:
        project = db.get(Project, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="project not found")

    revision_count = db.query(Revision).filter(Revision.project_id == project.id).count()
    revision = Revision(project_id=project.id, label=revision_label(revision_count))
    db.add(revision)
    db.commit()
    db.refresh(revision)

    storage = Storage()
    if is_2d:
        key = storage_key_for_2d(str(project.id), str(revision.id), "source.dxf")
    else:
        key = storage_key_for_3d(str(project.id), str(revision.id), f"source{ext}")

    data = await file.read()
    storage.write_bytes(key, data)
    if settings.s3_enabled:
        s3 = get_s3_client(settings)
        s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=file.content_type or "application/octet-stream")

    db_file = File(
        revision_id=revision.id,
        kind=kind,
        filename=file.filename,
        content_type=file.content_type,
        size=str(len(data)),
        storage_key=key,
    )
    db.add(db_file)

    if is_2d:
        job_type = JobType.DRAWING
        queue_name = "drawing"
        job_fn = process_drawing
    else:
        job_type = JobType.CAD_LOD0
        queue_name = "cad"
        job_fn = process_cad_lod0

    job = Job(revision_id=revision.id, type=job_type, status=JobStatus.QUEUED, queue=queue_name)
    db.add(job)
    db.commit()
    db.refresh(job)

    q = get_queue(queue_name)
    q.enqueue(job_fn, str(job.id), job_id=str(job.id))

    return UploadResponse(project_id=project.id, revision_id=revision.id, job_id=job.id)


@router.get("/status/{revision_id}", response_model=StatusResponse)
def status(revision_id: UUID, db: Session = Depends(get_db)):
    revision = db.get(Revision, revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail="revision not found")

    s3 = get_s3_presign_client(settings) if settings.s3_enabled else None

    jobs = revision.jobs
    artifacts = revision.artifacts

    return StatusResponse(
        revision_id=revision.id,
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
                "storage_key": a.storage_key,
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

