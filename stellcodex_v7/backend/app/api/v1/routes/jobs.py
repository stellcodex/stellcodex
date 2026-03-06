from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from rq.job import Job
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.queue import redis_conn
from app.security.deps import Principal, get_current_principal
from app.workers.tasks import enqueue_convert_file, enqueue_mesh2d3d_export, enqueue_ping_job

router = APIRouter(tags=["jobs"])


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    enqueued_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    origin: str | None
    timeout: int | None
    meta: dict | None
    result: str | None
    error: str | None


class JobEnqueueOut(BaseModel):
    job_id: str


class JobCreateIn(BaseModel):
    file_id: str
    job_type: str = Field(default="convert", pattern="^(convert|mesh2d3d|ping)$")


def _short_exc(exc_info: str | None) -> str | None:
    if not exc_info:
        return None
    lines = [line for line in exc_info.splitlines() if line.strip()]
    return lines[-1] if lines else None


@router.post("/ping", response_model=JobEnqueueOut)
def enqueue_ping():
    job_id = enqueue_ping_job()
    return JobEnqueueOut(job_id=job_id)


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("", response_model=JobEnqueueOut)
def enqueue_job_contract(
    data: JobCreateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if data.job_type == "ping":
        return JobEnqueueOut(job_id=enqueue_ping_job())

    file_row = db.query(UploadFileModel).filter(UploadFileModel.file_id == data.file_id).first()
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    if data.job_type == "mesh2d3d":
        return JobEnqueueOut(job_id=enqueue_mesh2d3d_export(file_row.file_id))
    return JobEnqueueOut(job_id=enqueue_convert_file(file_row.file_id))


@router.get("/{job_id}", response_model=JobStatusOut)
def get_job(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    result = None
    if job.result is not None:
        try:
            result = str(job.result)
        except Exception:
            result = "<unserializable>"

    return JobStatusOut(
        job_id=job.id,
        status=job.get_status(),
        enqueued_at=job.enqueued_at,
        started_at=job.started_at,
        ended_at=job.ended_at,
        origin=job.origin,
        timeout=job.timeout,
        meta=job.meta or None,
        result=result,
        error=_short_exc(job.exc_info),
    )
