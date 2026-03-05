#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


WORKSPACE = Path("/root/workspace")
HANDOFF_DIR = WORKSPACE / "handoff"
LIVE_MD_PATH = HANDOFF_DIR / "LIVE-CONTEXT.md"
LIVE_JSON_PATH = HANDOFF_DIR / "LIVE-CONTEXT.json"
STREAM_KEY = "stell:events:stream"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(ts: datetime | None = None) -> str:
    current = ts or utc_now()
    return current.isoformat().replace("+00:00", "Z")


def trim_text(text: str, limit: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 14].rstrip() + "\n...[truncated]"


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-") or "unknown"


def ensure_dirs() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def publish_checkpoint_event(agent: str, task: str, status: str, summary: str, next_step: str, files: list[str], artifacts: list[str]) -> None:
    snapshot = {
        "updated_at": utc_iso(),
        "agent": agent,
        "task": task,
        "status": status,
        "summary": summary.strip(),
        "next_step": next_step.strip(),
        "files": files,
        "artifacts": artifacts,
        "live_context_json": str(LIVE_JSON_PATH),
        "live_context_markdown": str(LIVE_MD_PATH),
    }
    event = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": "stellcodex.progress-checkpoint",
        "type": "system.context.checkpointed",
        "time": utc_iso(),
        "subject": f"checkpoint:{safe_slug(agent)}",
        "datacontenttype": "application/json",
        "correlation_id": str(uuid.uuid4()),
        "data": {
            "intent": "context-sync",
            "risk_level": "low",
            "destructive": False,
            "dsac_stage": "dry-run",
            "agent": agent,
            "task": task,
            "status": status,
            "summary": trim_text(summary, 1200),
            "next_step": trim_text(next_step, 400) if next_step else "",
            "files": files,
            "artifacts": artifacts,
            "live_context": snapshot,
            "live_context_json": str(LIVE_JSON_PATH),
            "live_context_markdown": str(LIVE_MD_PATH),
        },
    }
    try:
        payload = json.dumps(event, ensure_ascii=False)
        redis_cli = shutil.which("redis-cli")
        if redis_cli:
            cmd = [redis_cli, "XADD", STREAM_KEY, "*", "payload", payload]
        else:
            cmd = ["docker", "exec", "stellcodex-redis", "redis-cli", "XADD", STREAM_KEY, "*", "payload", payload]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=5)
    except Exception:
        # Checkpoint writing must remain durable even if event emission fails.
        return


def write_agent_status(
    agent: str,
    task: str,
    status: str,
    summary: str,
    next_step: str,
    files: list[str],
    artifacts: list[str],
    timestamp: datetime,
) -> Path:
    status_path = HANDOFF_DIR / f"{safe_slug(agent)}-status.md"
    lines = [
        "## Gorev",
        trim_text(task, 400),
        "",
        "## Durum",
        status,
        "",
        "## Sonuc Ozeti",
        trim_text(summary, 1200),
        "",
    ]
    if next_step:
        lines.extend(["## Siradaki Adim", trim_text(next_step, 400), ""])
    if files:
        lines.extend(["## Dosyalar", *files, ""])
    if artifacts:
        lines.extend(["## Artefaktlar", *artifacts, ""])
    lines.extend(["## Timestamp", utc_iso(timestamp), ""])
    status_path.write_text("\n".join(lines), encoding="utf-8")
    return status_path


def append_session_entry(
    agent: str,
    task: str,
    status: str,
    summary: str,
    next_step: str,
    files: list[str],
    artifacts: list[str],
    timestamp: datetime,
) -> Path:
    session_path = HANDOFF_DIR / f"SESSION-{timestamp.strftime('%Y-%m-%d')}.md"
    lines = [
        "",
        "---",
        f"## {timestamp.strftime('%H:%M:%SZ')} - {agent} - {status}",
        "",
        f"Task: {trim_text(task, 400)}",
        "",
        trim_text(summary, 1600),
        "",
    ]
    if next_step:
        lines.extend([f"Next: {trim_text(next_step, 400)}", ""])
    if files:
        lines.extend(["Files:", *[f"- {item}" for item in files], ""])
    if artifacts:
        lines.extend(["Artifacts:", *[f"- {item}" for item in artifacts], ""])
    with session_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return session_path


def write_live_context(
    agent: str,
    task: str,
    status: str,
    summary: str,
    next_step: str,
    files: list[str],
    artifacts: list[str],
    status_path: Path,
    session_path: Path,
    timestamp: datetime,
) -> None:
    payload = {
        "updated_at": utc_iso(timestamp),
        "agent": agent,
        "task": task,
        "status": status,
        "summary": summary.strip(),
        "next_step": next_step.strip(),
        "files": files,
        "artifacts": artifacts,
        "agent_status_path": str(status_path),
        "session_path": str(session_path),
    }
    LIVE_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    LIVE_MD_PATH.write_text(
        "\n".join(
            [
                "# LIVE CONTEXT",
                "",
                f"- Updated: {utc_iso(timestamp)}",
                f"- Agent: {agent}",
                f"- Task: {trim_text(task, 400)}",
                f"- Status: {status}",
                f"- Next: {trim_text(next_step or 'not-set', 400)}",
                f"- Agent status: {status_path}",
                f"- Session log: {session_path}",
                "",
                "## Summary",
                trim_text(summary, 1600),
                "",
                "## Files",
                *([f"- {item}" for item in files] or ["- none"]),
                "",
                "## Artifacts",
                *([f"- {item}" for item in artifacts] or ["- none"]),
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_checkpoint(
    *,
    agent: str,
    task: str,
    status: str,
    summary: str,
    next_step: str = "",
    files: list[str] | None = None,
    artifacts: list[str] | None = None,
) -> dict[str, str]:
    ensure_dirs()
    timestamp = utc_now()
    normalized_files = [item.strip() for item in (files or []) if item.strip()]
    normalized_artifacts = [item.strip() for item in (artifacts or []) if item.strip()]
    status_path = write_agent_status(
        agent=agent,
        task=task,
        status=status,
        summary=summary,
        next_step=next_step,
        files=normalized_files,
        artifacts=normalized_artifacts,
        timestamp=timestamp,
    )
    session_path = append_session_entry(
        agent=agent,
        task=task,
        status=status,
        summary=summary,
        next_step=next_step,
        files=normalized_files,
        artifacts=normalized_artifacts,
        timestamp=timestamp,
    )
    write_live_context(
        agent=agent,
        task=task,
        status=status,
        summary=summary,
        next_step=next_step,
        files=normalized_files,
        artifacts=normalized_artifacts,
        status_path=status_path,
        session_path=session_path,
        timestamp=timestamp,
    )
    publish_checkpoint_event(
        agent=agent,
        task=task,
        status=status,
        summary=summary,
        next_step=next_step,
        files=normalized_files,
        artifacts=normalized_artifacts,
    )
    return {
        "status_path": str(status_path),
        "session_path": str(session_path),
        "live_md_path": str(LIVE_MD_PATH),
        "live_json_path": str(LIVE_JSON_PATH),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write durable progress checkpoints for shared handoff.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--next-step", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = write_checkpoint(
        agent=args.agent,
        task=args.task,
        status=args.status,
        summary=args.summary,
        next_step=args.next_step,
        files=args.file,
        artifacts=args.artifact,
    )
    print(result["status_path"])
    print(result["session_path"])
    print(result["live_md_path"])
    print(result["live_json_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
