from __future__ import annotations

from pathlib import Path

from rq import Worker

from app.core.ids import normalize_scx_id
from ..db import SessionLocal
from ..models.core import File, Job
from ..models.file import UploadFile as UploadFileModel
from ..queue import redis_conn
from ..storage import Storage
from app.core.config import settings
from app.core.storage import get_s3_client
from .common import mark_job_done, mark_job_failed, mark_job_running, write_3d_artifacts


def _sync_legacy_file_status(db, rev_uid: str, status: str, error: str | None = None) -> None:
    file_id = normalize_scx_id(str(rev_uid))
    row = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if row is None:
        return
    row.status = status
    if error:
        row.meta = {**(row.meta or {}), "error": error}
    db.add(row)


def process_cad_lod0(job_id: str) -> None:
    storage = Storage()
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        mark_job_running(db, job)
        _sync_legacy_file_status(db, str(job.rev_uid), "running")
        db.commit()

        source_file = (
            db.query(File)
            .filter(File.rev_uid == job.rev_uid)
            .order_by(File.created_at.asc())
            .first()
        )
        if source_file is None:
            raise RuntimeError("source file not found")

        source_path = Path(storage.root / source_file.blob_path)
        if not source_path.exists() and settings.s3_enabled:
            source_path.parent.mkdir(parents=True, exist_ok=True)
            s3 = get_s3_client(settings)
            s3.download_file(settings.s3_bucket, source_file.blob_path, str(source_path))
        project_id = str(job.revision.project_id)
        rev_uid = str(job.rev_uid)
        write_3d_artifacts(db, storage, project_id, rev_uid, source_path)
        mark_job_done(db, job)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(Job, job_id)
        if job is not None:
            mark_job_failed(db, job, str(exc))
            _sync_legacy_file_status(db, str(job.rev_uid), "failed", str(exc))
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    worker = Worker(["cad"], connection=redis_conn)
    worker.work()
