from __future__ import annotations

import threading
import time

from app.services.ai_snapshot_jobs import backfill_legacy_snapshot_jobs, enqueue_due_snapshot_jobs
from app.workers.tasks import enqueue_retention_purge


def start_retention_scheduler(interval_seconds: int = 15 * 60) -> None:
    def _loop():
        while True:
            try:
                enqueue_retention_purge()
            except Exception:
                pass
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()


def start_snapshot_scheduler(interval_seconds: int = 30, backfill_limit: int = 200) -> None:
    def _loop():
        try:
            backfill_legacy_snapshot_jobs(limit=backfill_limit)
        except Exception:
            pass
        while True:
            try:
                enqueue_due_snapshot_jobs()
            except Exception:
                pass
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
