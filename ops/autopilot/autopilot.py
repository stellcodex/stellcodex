#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    temp.replace(path)


class Config:
    def __init__(self) -> None:
        self.jobs_root = Path(os.getenv("JOBS_ROOT", "/jobs"))
        self.workspace_root = Path(os.getenv("WORKSPACE_ROOT", "/workspace"))
        self.orchestra_url = os.getenv("ORCHESTRA_URL", "http://orchestrator:7010").rstrip("/")

        self.max_retries = int(os.getenv("MAX_RETRIES", os.getenv("AUTOPILOT_MAX_RETRIES", "5")))
        self.defer_retry_seconds = int(
            os.getenv("DEFER_RETRY_SECONDS", os.getenv("AUTOPILOT_DEFER_RETRY_SECONDS", "900"))
        )
        self.loop_sleep_seconds = int(
            os.getenv("LOOP_SLEEP_SECONDS", os.getenv("AUTOPILOT_LOOP_SECONDS", "5"))
        )
        self.scan_interval_seconds = int(
            os.getenv("SCAN_INTERVAL_SECONDS", os.getenv("AUTOPILOT_SCAN_INTERVAL_SECONDS", "600"))
        )
        self.http_timeout_seconds = int(os.getenv("AUTOPILOT_HTTP_TIMEOUT_SECONDS", "180"))
        self.daily_report_hour = int(os.getenv("DAILY_REPORT_HOUR", "9"))
        self.tz = ZoneInfo(os.getenv("TZ", "Europe/Istanbul"))

        self.inbox = self.jobs_root / "inbox"
        self.done = self.jobs_root / "done"
        self.failed = self.jobs_root / "failed"
        self.deferred = self.jobs_root / "deferred"
        self.output = self.jobs_root / "output"
        self.logs = self.jobs_root / "logs"
        self.backups = self.jobs_root / "backups"

        self.events_log = self.logs / "events.jsonl"
        self.retry_state_path = self.logs / "retry_state.json"
        self.auto_issue_state_path = self.logs / "auto_issue_state.json"
        self.scheduler_state_path = self.logs / "scheduler_state.json"
        self.lock_path = self.logs / "autopilot.lock"


class Autopilot:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.retry_state: Dict[str, int] = {}
        self.auto_issue_state: Dict[str, Any] = {"hashes": []}
        self.scheduler_state: Dict[str, Any] = {}
        self.last_scan_at: Optional[datetime] = None

    def ensure_dirs(self) -> None:
        for path in [
            self.cfg.jobs_root,
            self.cfg.inbox,
            self.cfg.done,
            self.cfg.failed,
            self.cfg.deferred,
            self.cfg.output,
            self.cfg.logs,
            self.cfg.backups,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        if not self.cfg.events_log.exists():
            self.cfg.events_log.touch()

        self.retry_state = read_json(self.cfg.retry_state_path, {})
        if not isinstance(self.retry_state, dict):
            self.retry_state = {}

        self.auto_issue_state = read_json(self.cfg.auto_issue_state_path, {"hashes": []})
        if not isinstance(self.auto_issue_state, dict):
            self.auto_issue_state = {"hashes": []}
        self.auto_issue_state.setdefault("hashes", [])

        self.scheduler_state = read_json(self.cfg.scheduler_state_path, {})
        if not isinstance(self.scheduler_state, dict):
            self.scheduler_state = {}

        self.cfg.lock_path.write_text(str(os.getpid()), encoding="utf-8")

    def _save_states(self) -> None:
        write_json(self.cfg.retry_state_path, self.retry_state)
        write_json(self.cfg.auto_issue_state_path, self.auto_issue_state)
        write_json(self.cfg.scheduler_state_path, self.scheduler_state)

    def log_event(self, event: Dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", to_iso(utcnow()))
        with self.cfg.events_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def _task_files(self, folder: Path) -> List[Path]:
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}]
        return sorted(files, key=lambda p: p.name)

    def _task_output_dir(self, task_id: str) -> Path:
        target = self.cfg.output / task_id
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _attempt_key(self, path: Path) -> str:
        return path.name

    def _task_id(self, path: Path) -> str:
        return path.stem

    def _attempt_count(self, path: Path) -> int:
        return int(self.retry_state.get(self._attempt_key(path), 0))

    def _set_attempt_count(self, path: Path, count: int) -> None:
        self.retry_state[self._attempt_key(path)] = int(count)

    def _clear_attempt_count(self, path: Path) -> None:
        self.retry_state.pop(self._attempt_key(path), None)

    def _write_status(
        self,
        *,
        task_id: str,
        source_file: str,
        status: str,
        attempts: int,
        detail: str,
        http_status: Optional[int] = None,
    ) -> None:
        payload = {
            "task_id": task_id,
            "source_file": source_file,
            "status": status,
            "attempts": attempts,
            "detail": detail,
            "http_status": http_status,
            "updated_at": to_iso(utcnow()),
        }
        write_json(self._task_output_dir(task_id) / "status.json", payload)

    def _write_outputs(self, task_id: str, payload: Dict[str, Any]) -> None:
        out_dir = self._task_output_dir(task_id)
        final_output = payload.get("final_output") or ((payload.get("final") or {}).get("output", ""))
        routing = payload.get("routing_decisions", [])
        results = payload.get("results", [])

        (out_dir / "final_output.md").write_text(str(final_output), encoding="utf-8")
        write_json(out_dir / "routing.json", routing)
        write_json(out_dir / "results.json", results)

    def _move_with_overwrite(self, source: Path, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            suffix = utcnow().strftime("%Y%m%d_%H%M%S")
            target = target_dir / f"{source.stem}_{suffix}{source.suffix}"
        shutil.move(str(source), str(target))
        return target

    def _deferred_meta_path(self, task_name: str) -> Path:
        return self.cfg.deferred / f"{task_name}.meta.json"

    def _mark_done(self, source: Path, payload: Dict[str, Any], attempts: int) -> None:
        task_id = self._task_id(source)
        self._write_outputs(task_id, payload)
        moved = self._move_with_overwrite(source, self.cfg.done)
        self._clear_attempt_count(source)
        self._clear_attempt_count(moved)
        self._write_status(
            task_id=task_id,
            source_file=moved.name,
            status="DONE",
            attempts=attempts,
            detail="processed",
            http_status=200,
        )
        self.log_event(
            {
                "event": "task_done",
                "task_id": task_id,
                "file": moved.name,
                "attempts": attempts,
            }
        )

    def _mark_deferred(
        self,
        source: Path,
        detail: str,
        attempts: int,
        payload: Optional[Dict[str, Any]],
    ) -> None:
        task_id = self._task_id(source)
        retry_at = utcnow() + timedelta(seconds=self.cfg.defer_retry_seconds)
        if payload:
            self._write_outputs(task_id, payload)

        moved = self._move_with_overwrite(source, self.cfg.deferred)
        write_json(
            self._deferred_meta_path(moved.name),
            {
                "task_id": task_id,
                "source_file": moved.name,
                "attempts": attempts,
                "detail": detail,
                "retry_at": to_iso(retry_at),
                "updated_at": to_iso(utcnow()),
            },
        )
        self._set_attempt_count(moved, attempts)
        self._write_status(
            task_id=task_id,
            source_file=moved.name,
            status="DEFERRED",
            attempts=attempts,
            detail=detail,
            http_status=429,
        )
        self.log_event(
            {
                "event": "task_deferred",
                "task_id": task_id,
                "file": moved.name,
                "attempts": attempts,
                "detail": detail,
            }
        )

    def _mark_failed(self, source: Path, detail: str, attempts: int, http_status: Optional[int]) -> None:
        task_id = self._task_id(source)
        moved = self._move_with_overwrite(source, self.cfg.failed)
        self._clear_attempt_count(source)
        self._clear_attempt_count(moved)
        self._write_status(
            task_id=task_id,
            source_file=moved.name,
            status="FAILED",
            attempts=attempts,
            detail=detail,
            http_status=http_status,
        )
        self.log_event(
            {
                "event": "task_failed",
                "task_id": task_id,
                "file": moved.name,
                "attempts": attempts,
                "detail": detail,
                "http_status": http_status,
            }
        )

    def _call_orchestrate(self, task_text: str, source_name: str) -> Tuple[int, Dict[str, Any], str]:
        payload = {
            "task": task_text,
            "context": {"source_file": source_name, "autopilot": True},
            "speed": "eco",
        }
        with httpx.Client(timeout=self.cfg.http_timeout_seconds) as client:
            response = client.post(
                f"{self.cfg.orchestra_url}/orchestrate",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
        text = response.text
        parsed: Dict[str, Any] = {}
        if text.strip():
            try:
                decoded = response.json()
                if isinstance(decoded, dict):
                    parsed = decoded
            except Exception:
                parsed = {}
        return response.status_code, parsed, text

    def _is_quota_deferred(self, status_code: int, payload: Dict[str, Any], raw_text: str) -> bool:
        if status_code == 429:
            return True
        deferred = payload.get("deferred") if isinstance(payload, dict) else None
        if isinstance(deferred, dict) and deferred.get("newly_deferred"):
            return True
        text = (raw_text or "").lower()
        return "quota" in text and "defer" in text

    def process_task(self, path: Path) -> None:
        task_id = self._task_id(path)
        task_text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not task_text:
            self._mark_failed(path, detail="empty_task", attempts=1, http_status=None)
            return

        current = self._attempt_count(path)
        for attempt in range(current + 1, self.cfg.max_retries + 1):
            self._set_attempt_count(path, attempt)
            self._save_states()

            try:
                status_code, payload, raw_text = self._call_orchestrate(task_text, path.name)
            except Exception as exc:
                detail = f"orchestrate_request_error:{exc.__class__.__name__}"
                if attempt >= self.cfg.max_retries:
                    self._mark_failed(path, detail=detail, attempts=attempt, http_status=None)
                    return
                self.log_event(
                    {
                        "event": "task_retry",
                        "task_id": task_id,
                        "file": path.name,
                        "attempt": attempt,
                        "detail": detail,
                    }
                )
                time.sleep(2)
                continue

            if status_code < 300 and payload:
                self._mark_done(path, payload, attempts=attempt)
                return

            detail = f"http_{status_code}" if status_code else "http_unknown"
            if self._is_quota_deferred(status_code, payload, raw_text):
                self._mark_deferred(path, detail=detail, attempts=attempt, payload=payload if payload else None)
                return

            if attempt >= self.cfg.max_retries:
                self._mark_failed(path, detail=detail, attempts=attempt, http_status=status_code)
                return

            self.log_event(
                {
                    "event": "task_retry",
                    "task_id": task_id,
                    "file": path.name,
                    "attempt": attempt,
                    "detail": detail,
                    "http_status": status_code,
                }
            )
            time.sleep(2)

    def _requeue_deferred(self) -> None:
        now = utcnow()
        for task_file in self._task_files(self.cfg.deferred):
            meta_path = self._deferred_meta_path(task_file.name)
            meta = read_json(meta_path, {})
            retry_at = parse_iso(meta.get("retry_at") if isinstance(meta, dict) else None)
            if retry_at and retry_at > now:
                continue

            moved = self._move_with_overwrite(task_file, self.cfg.inbox)
            attempts = int(meta.get("attempts", 0)) if isinstance(meta, dict) else 0
            self._set_attempt_count(moved, attempts)
            if meta_path.exists():
                meta_path.unlink(missing_ok=True)
            self.log_event(
                {
                    "event": "task_requeued",
                    "task_id": moved.stem,
                    "file": moved.name,
                    "attempts": attempts,
                }
            )

    def _run_cmd(self, command: List[str], timeout: int = 60) -> Tuple[int, str]:
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
            out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
            return proc.returncode, out.strip()
        except Exception as exc:
            return 1, f"{exc.__class__.__name__}: {exc}"

    def _normalized_lines(self, text: str, max_lines: int = 20) -> List[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        dedup: List[str] = []
        seen = set()
        for line in lines:
            if line in seen:
                continue
            seen.add(line)
            dedup.append(line)
            if len(dedup) >= max_lines:
                break
        return dedup

    def _issue_hash(self, category: str, title: str, locations: List[str]) -> str:
        body = f"{category}|{title}|{'|'.join(locations)}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _create_auto_issue(
        self,
        *,
        category: str,
        title: str,
        summary: str,
        locations: List[str],
        fix_requirements: str,
    ) -> Optional[Path]:
        issue_hash = self._issue_hash(category, title, locations)
        known = set(self.auto_issue_state.get("hashes", []))
        if issue_hash in known:
            return None

        ts = utcnow().strftime("%Y%m%d_%H%M%S")
        slug = "_".join(title.lower().split())[:48]
        task_path = self.cfg.inbox / f"AUTO_{ts}_{slug}.md"
        content = (
            "# AUTO-REMEDIATION TASK\n\n"
            f"Category: {category}\n"
            f"Title: {title}\n"
            f"Detected At: {to_iso(utcnow())}\n\n"
            f"## Problem Summary\n{summary}\n\n"
            "## File Locations\n"
            + "\n".join(f"- {loc}" for loc in locations)
            + "\n\n"
            f"## Fix Requirements\n{fix_requirements}\n\n"
            "## Rollback Note\n"
            "Revert only files touched by this fix and restart impacted services.\n"
        )
        task_path.write_text(content, encoding="utf-8")

        self.auto_issue_state.setdefault("hashes", []).append(issue_hash)
        self.log_event(
            {
                "event": "auto_issue_created",
                "category": category,
                "title": title,
                "task_file": task_path.name,
            }
        )
        return task_path

    def _scan_source_markers(self) -> None:
        root = str(self.cfg.workspace_root)
        exclude = [
            "--glob",
            "!**/.git/**",
            "--glob",
            "!**/node_modules/**",
            "--glob",
            "!**/_backups/**",
            "--glob",
            "!**/_archive/**",
            "--glob",
            "!**/.venv/**",
        ]

        cmd = ["rg", "-n", "TODO|FIXME|NOT IMPLEMENTED|HACK", root, *exclude]
        rc, output = self._run_cmd(cmd, timeout=120)
        if rc == 0 and output:
            locations = self._normalized_lines(output, max_lines=20)
            self._create_auto_issue(
                category="code_markers",
                title="todo_fixme_markers_detected",
                summary="Source markers indicate unfinished work remains in the codebase.",
                locations=locations,
                fix_requirements="Resolve each marker or convert it into tracked, tested behavior.",
            )

        ni_cmd = ["rg", "-n", "raise NotImplementedError|pass\\s*$", root, *exclude]
        rc, output = self._run_cmd(ni_cmd, timeout=120)
        if rc == 0 and output:
            locations = self._normalized_lines(output, max_lines=20)
            self._create_auto_issue(
                category="code_markers",
                title="not_implemented_patterns_detected",
                summary="NotImplementedError/pass stubs were found.",
                locations=locations,
                fix_requirements="Replace stubs with implementation and add smoke/unit checks.",
            )

    def _scan_import_health(self) -> None:
        targets = [self.cfg.workspace_root / "ops", self.cfg.workspace_root / "ops" / "orchestra"]
        args = ["python3", "-m", "compileall", "-q", *[str(p) for p in targets if p.exists()]]
        rc, output = self._run_cmd(args, timeout=120)
        if rc != 0:
            self._create_auto_issue(
                category="import_health",
                title="compileall_failed",
                summary="Python compile checks failed; syntax/import health is broken.",
                locations=self._normalized_lines(output, max_lines=20) or ["compileall output unavailable"],
                fix_requirements="Repair syntax/import issues and rerun compile checks.",
            )

    def _scan_runtime_logs(self) -> None:
        compose_file = self.cfg.workspace_root / "ops" / "orchestra" / "docker-compose.yml"
        if not compose_file.exists():
            return

        rc, output = self._run_cmd(
            ["docker", "compose", "-f", str(compose_file), "logs", "--tail", "200"],
            timeout=120,
        )
        if rc != 0 or not output:
            return

        lower = output.lower()
        findings: List[Tuple[str, str, str]] = []
        if "500" in lower:
            findings.append(("runtime_logs", "http_500_detected", "Runtime logs include HTTP 500 responses."))
        if "connection refused" in lower:
            findings.append(
                ("runtime_logs", "connection_refused_detected", "Runtime logs include connection refused errors.")
            )
        if "missing environment variable" in lower or "keyerror" in lower:
            findings.append(
                ("runtime_logs", "missing_env_detected", "Runtime logs indicate missing environment values.")
            )
        if lower.count(" 404 ") >= 5 or lower.count("http 404") >= 5:
            findings.append(("runtime_logs", "repeated_404_detected", "Runtime logs indicate repeated 404 loops."))

        if not findings:
            return

        locations = self._normalized_lines(output, max_lines=20)
        for category, title, summary in findings:
            self._create_auto_issue(
                category=category,
                title=title,
                summary=summary,
                locations=locations,
                fix_requirements="Fix the root cause in routes/config/env and verify via smoke checks.",
            )

    def run_auto_remediation_scan(self) -> None:
        self._scan_source_markers()
        self._scan_import_health()
        self._scan_runtime_logs()
        self.last_scan_at = utcnow()

    def _orchestrator_health(self) -> Tuple[bool, str]:
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(f"{self.cfg.orchestra_url}/state")
            return resp.status_code == 200, f"http_{resp.status_code}"
        except Exception as exc:
            return False, exc.__class__.__name__

    def _today_files_count(self, folder: Path) -> int:
        today = datetime.now(self.cfg.tz).date()
        count = 0
        for path in folder.glob("*"):
            if not path.is_file():
                continue
            local_date = datetime.fromtimestamp(path.stat().st_mtime, tz=self.cfg.tz).date()
            if local_date == today:
                count += 1
        return count

    def _collect_recent_errors(self, limit: int = 5) -> List[str]:
        if not self.cfg.events_log.exists():
            return []
        rows = self.cfg.events_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        found: List[str] = []
        for raw in reversed(rows):
            try:
                item = json.loads(raw)
            except Exception:
                continue
            if item.get("event") in {"task_failed", "task_deferred"}:
                found.append(f"{item.get('event')}: {item.get('file')} ({item.get('detail')})")
            if len(found) >= limit:
                break
        return list(reversed(found))

    def _collect_major_fixes(self, limit: int = 8) -> List[str]:
        items = sorted(
            [p for p in self.cfg.done.glob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt"}],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [item.name for item in items[:limit]]

    def _maybe_send_whatsapp(self, message: str) -> Tuple[bool, str]:
        token = os.getenv("WHATSAPP_TOKEN", "").strip()
        phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        to = os.getenv("WHATSAPP_TO", "").strip()
        if not (token and phone_id and to):
            return False, "credentials_missing"

        url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message[:4000]},
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
            if resp.status_code < 300:
                return True, "sent"
            return False, f"http_{resp.status_code}"
        except Exception as exc:
            return False, exc.__class__.__name__

    def _render_daily_report(self, report_date: str, health: str) -> str:
        completed_today = self._today_files_count(self.cfg.done)
        major_fixes = self._collect_major_fixes()
        recent_errors = self._collect_recent_errors()
        deferred_items = self._task_files(self.cfg.deferred)

        lines = [
            "# DAILY REPORT",
            "",
            f"Date: {report_date}",
            f"Generated At: {to_iso(utcnow())}",
            "",
            "## Task Summary",
            f"- Tasks completed today: {completed_today}",
            f"- Running: {len(self._task_files(self.cfg.inbox))}",
            f"- Deferred: {len(deferred_items)}",
            f"- Failed: {len(self._task_files(self.cfg.failed))}",
            "",
            "## Major Fixes",
        ]
        if major_fixes:
            lines.extend([f"- {item}" for item in major_fixes])
        else:
            lines.append("- none")

        lines.extend(["", "## Errors"])
        if recent_errors:
            lines.extend([f"- {item}" for item in recent_errors])
        else:
            lines.append("- none")

        lines.extend(["", "## Deferred Tasks"])
        if deferred_items:
            lines.extend([f"- {item.name}" for item in deferred_items[:20]])
        else:
            lines.append("- none")

        lines.extend(["", "## System Health", f"- {health}", ""])
        return "\n".join(lines)

    def maybe_run_daily_report(self) -> None:
        now_local = datetime.now(self.cfg.tz)
        date_key = now_local.strftime("%Y-%m-%d")
        if str(self.scheduler_state.get("last_daily_report", "")) == date_key:
            return
        if now_local.hour < self.cfg.daily_report_hour:
            return

        healthy, reason = self._orchestrator_health()
        health = "OK" if healthy else f"DEGRADED ({reason})"
        report_text = self._render_daily_report(date_key, health)

        report_path = self.cfg.logs / f"DAILY_REPORT_{date_key}.md"
        report_path.write_text(report_text, encoding="utf-8")

        sent, status = self._maybe_send_whatsapp(report_text)
        if not sent:
            pending = self.cfg.logs / f"WHATSAPP_PENDING_{date_key}.txt"
            pending.write_text(f"status={status}\n\n{report_text}\n", encoding="utf-8")

        self.scheduler_state["last_daily_report"] = date_key
        self._save_states()
        self.log_event(
            {
                "event": "daily_report_generated",
                "date": date_key,
                "whatsapp": "sent" if sent else f"pending:{status}",
            }
        )

    def run_once(self) -> None:
        self._requeue_deferred()

        for task_file in self._task_files(self.cfg.inbox):
            self.process_task(task_file)

        now = utcnow()
        if not self.last_scan_at or (now - self.last_scan_at).total_seconds() >= self.cfg.scan_interval_seconds:
            self.run_auto_remediation_scan()

        self.maybe_run_daily_report()
        self._save_states()

    def run_forever(self) -> None:
        self.ensure_dirs()
        self.log_event({"event": "autopilot_started", "pid": os.getpid()})
        while True:
            try:
                self.run_once()
            except Exception as exc:
                self.log_event(
                    {
                        "event": "autopilot_loop_error",
                        "error": exc.__class__.__name__,
                        "detail": str(exc)[:200],
                    }
                )
            time.sleep(max(self.cfg.loop_sleep_seconds, 1))


def main() -> None:
    pilot = Autopilot(Config())
    pilot.run_forever()


if __name__ == "__main__":
    main()
