from __future__ import annotations

from rq import Worker

from app.queue import redis_conn
from app.workers.scheduler import start_retention_scheduler


def main() -> None:
    start_retention_scheduler()
    worker = Worker(["cad", "drawing", "render"], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
