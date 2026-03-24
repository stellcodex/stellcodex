from __future__ import annotations

from rq import Worker

from app.core.config import settings
from app.queue import redis_conn
from app.workers.bootstrap import prepare_worker_runtime
from app.workers.scheduler import start_snapshot_scheduler


def main() -> None:
    prepare_worker_runtime()
    start_snapshot_scheduler()
    worker = Worker([settings.ai_snapshot_queue_name], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
