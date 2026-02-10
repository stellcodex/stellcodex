from pathlib import Path

from rq import Worker

from ..db import SessionLocal
from ..models.core import File, Job
from ..queue import redis_conn
from ..storage import Storage
from app.core.config import settings
from app.core.storage import get_s3_client
from .common import mark_job_done, mark_job_failed, mark_job_running, write_3d_artifacts


def process_cad_lod0(job_id: str) -> None:
    storage = Storage()
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        mark_job_running(db, job)
        db.commit()

        source_file = (
            db.query(File)
            .filter(File.revision_id == job.revision_id)
            .order_by(File.created_at.asc())
            .first()
        )
        if source_file is None:
            raise RuntimeError("source file not found")

        source_path = Path(storage.root / source_file.storage_key)
        if not source_path.exists() and settings.s3_enabled:
            source_path.parent.mkdir(parents=True, exist_ok=True)
            s3 = get_s3_client(settings)
            s3.download_file(settings.s3_bucket, source_file.storage_key, str(source_path))
        project_id = str(job.revision.project_id)
        revision_id = str(job.revision_id)
        write_3d_artifacts(db, storage, project_id, revision_id, source_path)
        mark_job_done(db, job)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(Job, job_id)
        if job is not None:
            mark_job_failed(db, job, str(exc))
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    worker = Worker(["cad"], connection=redis_conn)
    worker.work()
