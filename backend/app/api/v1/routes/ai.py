from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security.deps import Principal, require_role
from app.services.ai_learning import get_eval_summary, get_memory_stats, list_memory_cases, list_pattern_signals
from app.services.ai_snapshot_jobs import (
    SnapshotEnqueueError,
    get_snapshot_job_stats,
    list_snapshot_jobs,
    retry_snapshot_job,
)

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_role("admin"))])


@router.get("/memory/stats")
def ai_memory_stats(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    return get_memory_stats(db)


@router.get("/memory/cases")
def ai_memory_cases(
    type: str = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    try:
        return list_memory_cases(db, case_type=type, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/eval/summary")
def ai_eval_summary(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    return get_eval_summary(db, limit=limit)


@router.get("/patterns")
def ai_patterns(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    return list_pattern_signals(db, limit=limit)


@router.get("/snapshots/stats")
def ai_snapshot_stats(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    return get_snapshot_job_stats(db)


@router.get("/snapshots/jobs")
def ai_snapshot_jobs(
    status: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    return list_snapshot_jobs(db, status=status, limit=limit)


@router.post("/snapshots/jobs/{snapshot_job_id}/retry")
def ai_snapshot_retry(
    snapshot_job_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    _ = principal
    try:
        return retry_snapshot_job(db, snapshot_job_id=snapshot_job_id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))
    except SnapshotEnqueueError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc))
