from __future__ import annotations

import atexit
import os
import threading

from rq import Worker

from app.core.worker_registry import build_local_worker_snapshot, heartbeat_worker_node, set_worker_status, upsert_worker_node
from app.db.session import SessionLocal
from app.queue import redis_conn
from app.workers.scheduler import start_retention_scheduler


_WORKER_QUEUES = ["cad", "drawing", "render"]


def _with_registry_session(callback, **kwargs) -> None:
    db = SessionLocal()
    try:
        callback(db, **kwargs)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _start_worker_registry_heartbeat() -> tuple[str, threading.Event]:
    snapshot = build_local_worker_snapshot(queues=_WORKER_QUEUES)
    worker_id = str(snapshot["worker_id"])
    _with_registry_session(upsert_worker_node, **snapshot)

    stop_event = threading.Event()
    interval = max(15, int(os.getenv("STELLCODEX_WORKER_HEARTBEAT_SECONDS", "30") or "30"))

    def _heartbeat_loop() -> None:
        while not stop_event.wait(interval):
            _with_registry_session(heartbeat_worker_node, worker_id=worker_id, status="online")

    thread = threading.Thread(target=_heartbeat_loop, name="worker-registry-heartbeat", daemon=True)
    thread.start()
    return worker_id, stop_event


def main() -> None:
    start_retention_scheduler()
    worker_id, stop_event = _start_worker_registry_heartbeat()

    def _shutdown() -> None:
        stop_event.set()
        _with_registry_session(set_worker_status, worker_id=worker_id, status="offline")

    atexit.register(_shutdown)

    worker = Worker(_WORKER_QUEUES, connection=redis_conn)
    try:
        worker.work()
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
