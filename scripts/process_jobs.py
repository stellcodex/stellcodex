#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/workspace")
JOBS_DIR = ROOT / "_jobs"
INBOX_DIR = JOBS_DIR / "inbox"
PROCESSING_DIR = JOBS_DIR / "processing"
DONE_DIR = JOBS_DIR / "done"
FAILED_DIR = JOBS_DIR / "failed"
LOGS_DIR = JOBS_DIR / "logs"
EVENTS_PATH = LOGS_DIR / "events.jsonl"

sys.path.insert(0, str(ROOT / "scripts"))

from v10_final_execute import run_final_execution  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    for directory in (INBOX_DIR, PROCESSING_DIR, DONE_DIR, FAILED_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _log_event(event_type: str, **payload: Any) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {"at": _now(), "event": event_type, **payload}
    with EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=True) + "\n")


def _load_job(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _next_job() -> Path | None:
    jobs = sorted(INBOX_DIR.glob("*.json"))
    return jobs[0] if jobs else None


def main() -> int:
    _ensure_dirs()
    job_path = _next_job()
    if job_path is None:
        print(json.dumps({"status": "idle", "detail": "no job in inbox"}, ensure_ascii=True))
        return 0

    processing_path = PROCESSING_DIR / job_path.name
    job_path.replace(processing_path)
    job = _load_job(processing_path)
    job_id = str(job.get("job_id") or processing_path.stem)
    _log_event("job.started", job_id=job_id, job_type=job.get("job_type", "final_validation"), path=str(processing_path))

    try:
        result = run_final_execution(job=job, invoked_by="autopilot")
        final_payload = {
            **job,
            "completed_at": _now(),
            "system_closed": bool(result.get("system_closed")),
            "runs_path": str(ROOT / "_runs"),
        }
        destination = DONE_DIR / processing_path.name if result.get("system_closed") else FAILED_DIR / processing_path.name
        destination.write_text(json.dumps(final_payload, ensure_ascii=True, indent=2), encoding="utf-8")
        processing_path.unlink(missing_ok=True)
        _log_event(
            "job.completed" if result.get("system_closed") else "job.failed",
            job_id=job_id,
            system_closed=bool(result.get("system_closed")),
            path=str(destination),
        )
        print(json.dumps({"status": "done", "system_closed": bool(result.get("system_closed"))}, ensure_ascii=True))
        return 0 if result.get("system_closed") else 1
    except Exception as exc:
        destination = FAILED_DIR / processing_path.name
        destination.write_text(
            json.dumps({**job, "failed_at": _now(), "error": str(exc)}, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        processing_path.unlink(missing_ok=True)
        _log_event("job.failed", job_id=job_id, system_closed=False, error=str(exc), path=str(destination))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
