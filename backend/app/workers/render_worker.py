from rq import Worker

from ..db import SessionLocal
from ..models.core import Job
from ..queue import redis_conn
from ..storage import Storage
from ..core.render_presets import get_render_preset
from .common import mark_job_done, mark_job_failed, mark_job_running, write_render_artifact


def process_render(job_id: str, preset_name: str) -> None:
    storage = Storage()
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        mark_job_running(db, job)
        db.commit()

        # Validate preset from single-source config
        _preset = get_render_preset(preset_name)

        project_id = str(job.revision.project_id)
        revision_id = str(job.revision_id)
        write_render_artifact(db, storage, project_id, revision_id)
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
    worker = Worker(["render"], connection=redis_conn)
    worker.work()
