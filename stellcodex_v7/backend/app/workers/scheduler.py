from __future__ import annotations

import threading
import time

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
