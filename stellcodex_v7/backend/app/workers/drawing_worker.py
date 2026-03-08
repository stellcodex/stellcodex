from rq import Worker

from ..db import SessionLocal
from ..models.core import Job
from ..queue import redis_conn
from ..storage import Storage
from .common import mark_job_done, mark_job_failed, mark_job_running, write_drawing_artifacts


def process_drawing(job_id: str) -> None:
    storage = Storage()
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        mark_job_running(db, job)
        db.commit()

        project_id = str(job.revision.project_id)
        rev_uid = str(job.rev_uid)
        write_drawing_artifacts(db, storage, project_id, rev_uid)
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
    worker = Worker(["drawing"], connection=redis_conn)
    worker.work()
