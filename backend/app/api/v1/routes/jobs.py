from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from rq.job import Job

from app.queue import redis_conn

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


def _short_exc(exc_info: str | None) -> str | None:
    if not exc_info:
        return None
    lines = [line for line in exc_info.splitlines() if line.strip()]
    return lines[-1] if lines else None


@router.post("/ping", response_model=JobEnqueueOut)
def enqueue_ping():
    from app.workers.tasks import enqueue_ping_job

    job_id = enqueue_ping_job()
    return JobEnqueueOut(job_id=job_id)


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
