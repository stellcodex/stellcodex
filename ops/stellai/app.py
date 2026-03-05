from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo


JOBS_ROOT = Path(os.getenv("JOBS_ROOT", "/jobs"))
EVENTS_PATH = Path(os.getenv("EVENTS_PATH", "/jobs/logs/events.jsonl"))
ORCHESTRA_STATE_URL = os.getenv("ORCHESTRA_STATE_URL", "http://orchestrator:7010/state")
TZ = ZoneInfo(os.getenv("TZ", "Europe/Istanbul"))


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


app = FastAPI(title="STELL.AI", version="1.0.0")


def _task_files(path: Path) -> List[Path]:
    if not path.exists():
        return []
    return sorted(
        [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}],
        key=lambda p: p.name,
    )


def _count_today(files: List[Path]) -> int:
    today = datetime.now(TZ).date()
    count = 0
    for item in files:
        file_date = datetime.fromtimestamp(item.stat().st_mtime, tz=TZ).date()
        if file_date == today:
            count += 1
    return count


def _recent_events(limit: int = 10) -> List[Dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    lines = EVENTS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    items: List[Dict[str, Any]] = []
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            items.append(payload)
        if len(items) >= limit:
            break
    return list(reversed(items))


async def _orchestra_state() -> Tuple[bool, Dict[str, Any], str]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(ORCHESTRA_STATE_URL)
        if response.status_code >= 300:
            return False, {}, f"http_{response.status_code}"
        payload = response.json()
        if isinstance(payload, dict):
            return True, payload, "ok"
        return False, {}, "invalid_json"
    except Exception as exc:
        return False, {}, exc.__class__.__name__


async def _build_status_summary() -> Dict[str, Any]:
    inbox = _task_files(JOBS_ROOT / "inbox")
    done = _task_files(JOBS_ROOT / "done")
    deferred = _task_files(JOBS_ROOT / "deferred")
    failed = _task_files(JOBS_ROOT / "failed")

    ok, state, reason = await _orchestra_state()
    completed_today = _count_today(done)
    health = "OK" if ok else f"DEGRADED ({reason})"

    report_lines = [
        "STELL REPORT",
        "",
        f"Completed today: {completed_today}",
        f"Running: {len(inbox)}",
        f"Deferred: {len(deferred)}",
        f"Failed: {len(failed)}",
        f"Remaining: {len(inbox) + len(deferred)}",
        "",
        f"System health: {health}",
    ]

    return {
        "completed_today": completed_today,
        "running": len(inbox),
        "deferred": len(deferred),
        "failed": len(failed),
        "remaining": len(inbox) + len(deferred),
        "system_health": health,
        "orchestra_state": state,
        "recent_events": _recent_events(),
        "report": "\n".join(report_lines),
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    ok, _state, reason = await _orchestra_state()
    return {
        "ok": ok,
        "service": "stellai",
        "reason": reason,
    }


@app.get("/stellai/status")
async def stellai_status() -> Dict[str, Any]:
    return await _build_status_summary()


@app.post("/stellai/ask")
async def stellai_ask(payload: AskRequest) -> Dict[str, Any]:
    summary = await _build_status_summary()
    question = payload.question.strip().lower()

    if "durum" in question or "status" in question or "health" in question:
        answer = summary["report"]
    else:
        answer = (
            "STELL.AI task execution yapmaz; sistem durumunu raporlar.\n\n"
            + summary["report"]
        )

    return {
        "question": payload.question,
        "answer": answer,
        "summary": summary,
    }
