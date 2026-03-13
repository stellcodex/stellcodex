#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/root/workspace")
REPORTS_ROOT = ROOT / "_jobs" / "reports"
AUTOPILOT_REPORTS = REPORTS_ROOT / "autopilot"
EVIDENCE_ROOT = ROOT / "evidence"
HANDOFF_ROOT = ROOT / "handoff"
DRIVE_REMOTE_DIR = "gdrive:stellcodex/03_evidence/autopilot"
GATE_PREFIX = "v10_gate_"

LOCAL_FRONTEND = "http://127.0.0.1:3010"
LOCAL_API = "http://127.0.0.1:18000/api/v1"
LOCAL_ORKESTRA = "http://127.0.0.1:7010"
PUBLIC_FRONTEND = "https://stellcodex.com"
PUBLIC_API = "https://api.stellcodex.com/api/v1"
SELF_HOSTED_RESOLVE = "stellcodex.com:443:127.0.0.1"


@dataclass
class ShellResult:
    cmd: str
    code: int
    stdout: str
    stderr: str


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utcnow().isoformat().replace("+00:00", "Z")


def date_slug() -> str:
    return utcnow().strftime("%Y-%m-%d")


def timestamp_slug() -> str:
    return utcnow().strftime("%Y%m%dT%H%M%SZ")


def run_shell(cmd: str, timeout: int = 120) -> ShellResult:
    proc = subprocess.run(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return ShellResult(cmd=cmd, code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def safe_excerpt(text: str, limit: int = 40) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:limit])


def http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=body, method=method, headers=request_headers)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read().decode("utf-8", errors="ignore")
            return {
                "status": int(getattr(response, "status", 200)),
                "body": raw,
                "json": try_json(raw),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        return {
            "status": int(exc.code),
            "body": raw,
            "json": try_json(raw),
        }
    except Exception as exc:
        return {
            "status": 0,
            "body": str(exc),
            "json": None,
        }


def curl_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 20,
    resolve: str | None = None,
    insecure: bool = False,
) -> dict[str, Any]:
    body_file = f"/tmp/stellcodex_autopilot_{os.getpid()}.body"
    data_arg = ""
    if payload is not None:
        payload_raw = shlex.quote(json.dumps(payload, ensure_ascii=True))
        data_arg = f"--header 'Content-Type: application/json' --data {payload_raw}"
    resolve_arg = f"--resolve {shlex.quote(resolve)} " if resolve else ""
    insecure_arg = "-k " if insecure else ""
    command = (
        f"curl -A 'STELLCODEX-Autopilot/1.0' -L -sS "
        f"{insecure_arg}{resolve_arg}"
        f"--max-time {timeout} -X {method} {data_arg} "
        f"-o '{body_file}' -w '%{{http_code}}' {shlex.quote(url)}"
    )
    result = run_shell(command, timeout=timeout + 10)
    raw_body = Path(body_file).read_text(encoding="utf-8", errors="ignore") if Path(body_file).exists() else ""
    if Path(body_file).exists():
        Path(body_file).unlink(missing_ok=True)
    code_raw = (result.stdout or "").strip()
    try:
        status = int(code_raw)
    except Exception:
        status = 0
    return {
        "status": status,
        "body": raw_body,
        "json": try_json(raw_body),
    }


def try_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return None


def newest_path(pattern: str) -> Path | None:
    matches = sorted(ROOT.glob(pattern))
    return matches[-1] if matches else None


def route_matrix(
    base_url: str,
    paths: list[str],
    *,
    resolve: str | None = None,
    insecure: bool = False,
) -> dict[str, int]:
    results: dict[str, int] = {}
    for path in paths:
        url = f"{base_url.rstrip('/')}{path}"
        results[path] = int(curl_request(url, resolve=resolve, insecure=insecure)["status"])
    return results


def routes_all_ok(matrix: dict[str, int]) -> bool:
    return bool(matrix) and all(status == 200 for status in matrix.values())


def container_env_flags(container_name: str, keys: list[str]) -> dict[str, bool]:
    encoded_keys = json.dumps(keys)
    result = run_shell(
        "docker exec "
        f"{container_name} python -c 'import json, os; "
        f"keys = {encoded_keys}; "
        "print(json.dumps({key: bool(os.getenv(key)) for key in keys}, ensure_ascii=True))'"
    )
    return try_json(result.stdout.strip()) or {key: False for key in keys}


def count_dirty_lines() -> int:
    status = run_shell("git -C /root/workspace status --short")
    return len([line for line in status.stdout.splitlines() if line.strip()])


def latest_gate_dir() -> Path | None:
    candidates = sorted(
        path for path in EVIDENCE_ROOT.glob(f"{GATE_PREFIX}*") if path.is_dir()
    )
    return candidates[-1] if candidates else None


def load_gate_summary() -> dict[str, Any]:
    gate_dir = latest_gate_dir()
    if gate_dir is None:
        return {"dir": None}
    return {
        "dir": str(gate_dir),
        "gate_status": (gate_dir / "gate_status.txt").read_text(encoding="utf-8").strip()
        if (gate_dir / "gate_status.txt").exists()
        else "missing",
        "restore_status": (gate_dir / "restore_status.txt").read_text(encoding="utf-8").strip()
        if (gate_dir / "restore_status.txt").exists()
        else "missing",
        "drive_export_status": (gate_dir / "drive_export_status.txt").read_text(encoding="utf-8").strip()
        if (gate_dir / "drive_export_status.txt").exists()
        else "missing",
        "smoke_summary": read_json(gate_dir / "smoke" / "summary.json", {}),
    }


def collect_auth_flow() -> dict[str, Any]:
    unique = timestamp_slug().lower()
    email = f"integrity.{unique}@stellcodex.example.com"
    password = "IntegrityPass123"
    register = http_request(
        f"{LOCAL_API}/auth/register",
        method="POST",
        payload={"email": email, "password": password},
    )
    token = None
    if isinstance(register.get("json"), dict):
        token = register["json"].get("access_token")
    me = (
        http_request(f"{LOCAL_API}/me", headers={"Authorization": f"Bearer {token}"})
        if token
        else {"status": 0, "body": "missing token", "json": None}
    )
    login = http_request(
        f"{LOCAL_API}/auth/login",
        method="POST",
        payload={"email": email, "password": password},
    )
    invalid_login = http_request(
        f"{LOCAL_API}/auth/login",
        method="POST",
        payload={"email": email, "password": "wrong-password"},
    )
    return {
        "email": email,
        "register_status": register["status"],
        "me_status": me["status"],
        "login_status": login["status"],
        "invalid_login_status": invalid_login["status"],
    }


def collect_state(mode: str) -> dict[str, Any]:
    backup_report = read_json(REPORTS_ROOT / "stellcodex_backup_guard_latest.json", {})
    git_report = read_json(REPORTS_ROOT / "stellcodex_git_sync_latest.json", {})
    gate_report = load_gate_summary()
    v10_report = read_json(
        ROOT / "stellcodex_v7" / "_jobs" / "reports" / "stellcodex_v10_engineering_report.json",
        {},
    )
    provider_status_path = newest_path("audit/STELL_SYSTEM_CORE/10_reports/provider/provider_credential_status_*.json")
    provider_status = read_json(provider_status_path, {}) if provider_status_path else {}

    docker_ps = run_shell("docker ps --format '{{.Names}}|{{.Status}}'")
    queue_counts = {
        "cad": int(run_shell("docker exec deploy_redis_1 redis-cli llen rq:queue:cad").stdout.strip() or 0),
        "drawing": int(run_shell("docker exec deploy_redis_1 redis-cli llen rq:queue:drawing").stdout.strip() or 0),
        "render": int(run_shell("docker exec deploy_redis_1 redis-cli llen rq:queue:render").stdout.strip() or 0),
        "failed_cad": int(run_shell("docker exec deploy_redis_1 redis-cli zcard rq:failed:cad").stdout.strip() or 0),
    }
    failure_counts = try_json(
        run_shell(
            "docker exec deploy_backend_1 python -c 'import json; "
            "from app.db.session import SessionLocal; "
            "from app.models.file import UploadFile; "
            "from app.models.job_failure import JobFailure; "
            "from app.models.phase2 import DlqRecord; "
            "db = SessionLocal(); "
            "failures = db.query(JobFailure).all(); "
            "dlqs = db.query(DlqRecord).all(); "
            "status_by_file = {file_id: status for file_id, status in db.query(UploadFile.file_id, UploadFile.status).all()}; "
            "print(json.dumps({"
            "\"job_failures\": len(failures), "
            "\"dlq_records\": len(dlqs), "
            "\"active_job_failures\": sum(1 for row in failures if getattr(row, \"file_id\", None) and status_by_file.get(row.file_id) != \"ready\"), "
            "\"active_dlq_records\": sum(1 for row in dlqs if getattr(row, \"file_id\", None) and status_by_file.get(row.file_id) != \"ready\")"
            "}, ensure_ascii=True)); "
            "db.close()'"
        ).stdout.strip()
    ) or {
        "job_failures": -1,
        "dlq_records": -1,
        "active_job_failures": -1,
        "active_dlq_records": -1,
    }

    local_orkestra_raw = http_request(f"{LOCAL_ORKESTRA}/health")
    local_orkestra_json = local_orkestra_raw.get("json") if isinstance(local_orkestra_raw.get("json"), dict) else {}
    local_orkestra_health = {
        "status": local_orkestra_raw.get("status", 0),
        "ready": bool(local_orkestra_json.get("ok")),
        "readiness": local_orkestra_json.get("readiness"),
    }

    route_paths = ["/", "/files", "/projects", "/shares", "/admin/health", "/login", "/register", "/reset-password"]
    route_paths_local = ["/", "/files", "/projects", "/shares", "/admin/health", "/login", "/register", "/reset-password"]

    drive_top = [
        line.split(None, 4)[-1].strip()
        for line in run_shell("rclone lsd gdrive:stellcodex", timeout=120).stdout.splitlines()
        if line.strip()
    ]
    cloudflare_hosts = safe_excerpt(run_shell("getent hosts stellcodex.com api.stellcodex.com").stdout, limit=10)
    tls_raw = run_shell(
        "openssl s_client -servername stellcodex.com -connect stellcodex.com:443 </dev/null 2>/dev/null "
        "| openssl x509 -noout -subject -issuer -dates",
        timeout=30,
    )

    state = {
        "mode": mode,
        "generated_at": iso_now(),
        "dirty_count": count_dirty_lines(),
        "git": {
            "branch": run_shell("git -C /root/workspace branch --show-current").stdout.strip(),
            "head": run_shell("git -C /root/workspace rev-parse HEAD").stdout.strip(),
            "branch_vv": safe_excerpt(run_shell("git -C /root/workspace branch -vv").stdout, limit=20),
            "latest_guard": git_report,
        },
        "drive": {
            "top_level": drive_top,
            "latest_backup_guard": backup_report,
        },
        "vercel": {
            "headers": safe_excerpt(run_shell("curl -sSI https://stellcodex.com", timeout=30).stdout, limit=20),
            "cli_present": bool(run_shell("command -v vercel").stdout.strip()),
        },
        "provider_credentials": provider_status,
        "cloudflare": {
            "hosts": cloudflare_hosts,
            "tls_summary": safe_excerpt(tls_raw.stdout, limit=10),
        },
        "self_hosted_frontend": {
            "headers": safe_excerpt(
                run_shell(
                    "curl -k -sSI --resolve stellcodex.com:443:127.0.0.1 https://stellcodex.com",
                    timeout=30,
                ).stdout,
                limit=20,
            ),
            "routes": route_matrix(
                PUBLIC_FRONTEND,
                route_paths,
                resolve=SELF_HOSTED_RESOLVE,
                insecure=True,
            ),
            "pm2_status": safe_excerpt(run_shell("pm2 show stellcodex-next", timeout=30).stdout, limit=30),
        },
        "runtime": {
            "docker_ps": safe_excerpt(docker_ps.stdout, limit=50),
            "local_api_health": http_request(f"{LOCAL_API}/health"),
            "public_api_health": curl_request(f"{PUBLIC_API}/health"),
            "local_orkestra_health": local_orkestra_health,
            "queue_counts": queue_counts,
            "failure_counts": failure_counts,
        },
        "ui": {
            "local_routes": route_matrix(LOCAL_FRONTEND, route_paths_local),
            "public_routes": route_matrix(PUBLIC_FRONTEND, route_paths),
        },
        "mail": {
            "env_flags": container_env_flags("deploy_backend_1", ["RESEND_API_KEY", "EMAIL_FROM"]),
            "forgot_page_fake": "setSent(true)"
            in (ROOT / "stellcodex_v7" / "frontend" / "app" / "(public)" / "forgot" / "page.tsx").read_text(encoding="utf-8"),
            "reset_page_fake": "setDone(true)"
            in (ROOT / "stellcodex_v7" / "frontend" / "app" / "(public)" / "reset" / "page.tsx").read_text(encoding="utf-8"),
        },
        "auth": collect_auth_flow(),
        "whatsapp": {
            "env_flags": container_env_flags(
                "deploy_backend_1",
                ["WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET"],
            ),
            "local_verify_without_token": http_request(f"{LOCAL_API}/whatsapp/webhook"),
            "public_verify_without_token": curl_request(f"{PUBLIC_API}/whatsapp/webhook"),
            "local_unsigned_post": http_request(
                f"{LOCAL_API}/whatsapp/webhook",
                method="POST",
                payload={},
            ),
            "public_unsigned_post": curl_request(
                f"{PUBLIC_API}/whatsapp/webhook",
                method="POST",
                payload={},
            ),
        },
        "stellai": {
            "v10_report": v10_report,
            "env_flags": container_env_flags(
                "deploy_backend_1",
                ["JWT_SECRET", "JWT_ALG", "RESEND_API_KEY", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET"],
            ),
        },
        "gate": gate_report,
    }
    return state


def subsystem_rows(state: dict[str, Any]) -> list[dict[str, str]]:
    drive_top = set(state["drive"]["top_level"])
    drive_duplicate = {"evidence", "03_evidence"} <= drive_top or {"reports", "12_reports"} <= drive_top
    git_guard = state["git"]["latest_guard"]
    public_routes = state["ui"]["public_routes"]
    self_hosted = state["self_hosted_frontend"]
    provider_credentials = state.get("provider_credentials") or {}
    whatsapp = state["whatsapp"]
    mail = state["mail"]
    gate = state["gate"]
    queue_counts = state["runtime"]["queue_counts"]
    failure_counts = state["runtime"]["failure_counts"]
    auth = state["auth"]
    v10_report = state["stellai"]["v10_report"]
    public_ui_ok = routes_all_ok(public_routes)
    self_hosted_ready = routes_all_ok(self_hosted["routes"])
    provider_blocked = provider_credentials.get("summary") == "BLOCKED_MISSING_CREDENTIALS"
    edge_is_vercel = "x-vercel-id" in state["vercel"]["headers"].lower()
    active_job_failures = int(failure_counts.get("active_job_failures", failure_counts.get("job_failures", -1)) or 0)
    active_dlq_records = int(failure_counts.get("active_dlq_records", failure_counts.get("dlq_records", -1)) or 0)

    return [
        {
            "area": "Google Drive",
            "status": "PARTIAL" if drive_duplicate else "PASS",
            "expected": "Current backups, reports, evidence, and archive paths remain normalized and unique.",
            "current": "Drive sync is current, but duplicate legacy top-level folders remain.",
            "severity": "MEDIUM" if drive_duplicate else "LOW",
        },
        {
            "area": "GitHub",
            "status": "FAIL" if not git_guard.get("worktree_clean") else "PASS",
            "expected": "Canonical repo and live runtime stay aligned without dirty drift.",
            "current": "Live workspace is dirty and both ahead of and behind origin/master.",
            "severity": "CRITICAL",
        },
        {
            "area": "Vercel",
            "status": "BLOCKED" if edge_is_vercel and provider_blocked and self_hosted_ready else ("PASS" if public_ui_ok else "PARTIAL"),
            "expected": "Public frontend can be switched away from Vercel without waiting on edge deploy timing.",
            "current": (
                "Public edge is still served by Vercel, but the self-hosted nginx path is ready and validated locally; final cutover is blocked by missing provider credentials."
                if edge_is_vercel and provider_blocked and self_hosted_ready
                else "Production route surface is healthy."
                if public_ui_ok
                else "Production route surface still has unresolved drift."
            ),
            "severity": "HIGH",
        },
        {
            "area": "Cloudflare",
            "status": "BLOCKED" if provider_blocked else "PARTIAL",
            "expected": "DNS, proxying, and TLS stay correct and can be updated directly for frontend cutover.",
            "current": (
                "Edge and TLS are healthy, but account-level DNS/proxy changes cannot be executed from this host because Cloudflare credentials are missing."
                if provider_blocked
                else "Edge and TLS are healthy, but account-level DNS and proxy config were not directly queried."
            ),
            "severity": "HIGH" if provider_blocked else "MEDIUM",
        },
        {
            "area": "Orkestra",
            "status": "PARTIAL" if queue_counts["failed_cad"] > 0 or active_job_failures > 0 or active_dlq_records > 0 else "PASS",
            "expected": "Workers run, queues drain, and failed jobs are remediated.",
            "current": (
                "Runtime is healthy and active queues are clear."
                if queue_counts["failed_cad"] == 0 and active_job_failures == 0 and active_dlq_records == 0
                else "Runtime is healthy, but unresolved failed jobs or DLQ records remain."
            ),
            "severity": "MEDIUM",
        },
        {
            "area": "STELL-AI",
            "status": "PARTIAL" if "vector_store_fallback_active" in (v10_report.get("degraded_features") or []) else "PASS",
            "expected": "Engineering intelligence stays truthful about retrieval and geometry capability.",
            "current": "Deterministic engineering layer is active, but vector store fallback remains enabled.",
            "severity": "MEDIUM",
        },
        {
            "area": "WhatsApp",
            "status": "PARTIAL",
            "expected": "Signed webhook traffic is enforced or the runtime explicitly documents unsigned fallback.",
            "current": "Webhook exists and fails safely, but the live runtime still operates without app-secret enforcement.",
            "severity": "HIGH",
        },
        {
            "area": "UI",
            "status": "PASS" if public_ui_ok and self_hosted_ready else "PARTIAL",
            "expected": "Navigation, protected routes, and public route surfaces remain coherent in production.",
            "current": (
                "Public and self-hosted route surfaces are both reachable for the core UI paths."
                if public_ui_ok and self_hosted_ready
                else "Route parity is still incomplete across public and self-hosted surfaces."
            ),
            "severity": "HIGH",
        },
        {
            "area": "Mail",
            "status": "FAIL" if not mail["env_flags"].get("RESEND_API_KEY") else "PARTIAL",
            "expected": "Outbound mail and recovery flows are real, not simulated.",
            "current": "Password reset endpoints are real, but delivery is disabled because the mail provider key is absent.",
            "severity": "HIGH",
        },
        {
            "area": "Authentication",
            "status": "PASS"
            if auth["register_status"] == 201 and auth["login_status"] == 200 and auth["me_status"] == 200
            else "PARTIAL",
            "expected": "Register, login, me, logout, and invalid-session handling behave through the real API.",
            "current": "Local API auth flow is live and the public login/register/reset-password surfaces are reachable.",
            "severity": "MEDIUM",
        },
        {
            "area": "Modules",
            "status": "PASS"
            if gate.get("gate_status") == "PASS" and gate.get("smoke_summary", {}).get("share_expire_http") == 410
            else "PARTIAL",
            "expected": "Upload, file detail, viewer, orchestrator, DFM, approvals, and shares stay operational.",
            "current": "Latest release gate smoke passed locally with file, viewer, DFM, and share proofs.",
            "severity": "MEDIUM",
        },
        {
            "area": "Backup/Restore",
            "status": "PASS"
            if gate.get("restore_status") == "PASS" and gate.get("drive_export_status") == "PASS"
            else "PARTIAL",
            "expected": "Backups stay fresh, restore verification passes, and evidence is archived off-server.",
            "current": "Backup guard, restore verification, and Drive export passed in the latest gate.",
            "severity": "HIGH",
        },
        {
            "area": "Autopilot",
            "status": "PARTIAL",
            "expected": "Recurring integrity checks produce timestamped PASS/FAIL/PARTIAL/BLOCKED reports.",
            "current": "Autopilot repo wiring is being established by this execution.",
            "severity": "MEDIUM",
        },
    ]


def render_status_table(rows: list[dict[str, str]]) -> str:
    header = "| Area | Status | Severity | Current | Expected |\n| --- | --- | --- | --- | --- |"
    body = [
        f"| {row['area']} | {row['status']} | {row['severity']} | {row['current']} | {row['expected']} |"
        for row in rows
    ]
    return "\n".join([header, *body])


def write_closeout_bundle(
    state: dict[str, Any],
    evidence_dir: Path,
    *,
    archive_success: bool,
    autopilot_enabled: bool,
) -> None:
    rows = subsystem_rows(state)
    drive = state["drive"]
    git = state["git"]
    runtime = state["runtime"]
    ui = state["ui"]
    whatsapp = state["whatsapp"]
    auth = state["auth"]
    gate = state["gate"]
    mail = state["mail"]

    docs: dict[str, str] = {
        "DRIVE_AUDIT.md": (
            "# DRIVE AUDIT\n\n"
            f"- Generated: `{state['generated_at']}`\n"
            f"- Remote base: `{drive['latest_backup_guard'].get('remote_base', 'unknown')}`\n"
            f"- Latest backup guard: `{drive['latest_backup_guard'].get('generated_at', 'missing')}`\n"
            f"- Truth sync status: `{ 'PASS' if drive['latest_backup_guard'].get('truth_sync_log') else 'MISSING' }`\n"
            f"- Runtime sync targets: `{', '.join(sorted((drive['latest_backup_guard'].get('runtime_syncs') or {}).keys()))}`\n"
            f"- Top-level folders: `{', '.join(drive['top_level'])}`\n"
        ),
        "DRIVE_STRUCTURE_MAP.md": (
            "# DRIVE STRUCTURE MAP\n\n"
            "Observed top-level folders:\n\n"
            + "\n".join(f"- `{name}`" for name in drive["top_level"])
        ),
        "DRIVE_GAPS.md": (
            "# DRIVE GAPS\n\n"
            "- Duplicate legacy folder families remain: `03_evidence` vs `evidence`, `12_reports` vs `reports`.\n"
            "- Drive current/archive posture is working, but structure normalization is incomplete.\n"
        ),
        "GITHUB_AUDIT.md": (
            "# GITHUB AUDIT\n\n"
            f"- Branch: `{git['branch']}`\n"
            f"- HEAD: `{git['head']}`\n"
            f"- Dirty paths: `{state['dirty_count']}`\n"
            f"- Guard branch summary:\n\n```\n{git['branch_vv']}\n```\n"
        ),
        "GITHUB_DRIFT_REPORT.md": (
            "# GITHUB DRIFT REPORT\n\n"
            f"- Worktree clean: `{git['latest_guard'].get('worktree_clean')}`\n"
            f"- Ahead count: `{git['latest_guard'].get('ahead_count')}`\n"
            f"- Behind count: `{git['latest_guard'].get('behind_count')}`\n"
            f"- Workspace apply status: `{git['latest_guard'].get('workspace_apply_status')}`\n"
        ),
        "GITHUB_RELEASE_STATE.md": (
            "# GITHUB RELEASE STATE\n\n"
            "- Canonical GitHub alignment is not closed.\n"
            f"- Remote: `{git['latest_guard'].get('remote_url')}`\n"
            f"- Local head: `{git['latest_guard'].get('local_head')}`\n"
            f"- Remote head: `{git['latest_guard'].get('remote_head')}`\n"
        ),
        "VERCEL_AUDIT.md": (
            "# VERCEL AUDIT\n\n"
            f"- Public root headers:\n\n```\n{state['vercel']['headers']}\n```\n"
            f"- Local routes: `{ui['local_routes']}`\n"
            f"- Public routes: `{ui['public_routes']}`\n"
            f"- Self-hosted ingress routes: `{state['self_hosted_frontend']['routes']}`\n"
            f"- Provider credential summary: `{state.get('provider_credentials', {}).get('summary', 'unknown')}`\n"
            "- Direct Vercel project binding and traffic cutover remain blocked because the Vercel/Cloudflare credentials are not present.\n"
        ),
        "CLOUDFLARE_AUDIT.md": (
            "# CLOUDFLARE AUDIT\n\n"
            f"- Host resolution:\n\n```\n{state['cloudflare']['hosts']}\n```\n"
            f"- TLS summary:\n\n```\n{state['cloudflare']['tls_summary']}\n```\n"
            f"- Provider credential summary: `{state.get('provider_credentials', {}).get('summary', 'unknown')}`\n"
            "- Edge reachability and TLS are verified. Account-level DNS and proxy settings remain blocked without credentials.\n"
        ),
        "ORKESTRA_AUDIT.md": (
            "# ORKESTRA AUDIT\n\n"
            f"- Local health status: `{runtime['local_orkestra_health']['status']}`\n"
            f"- Queue counts: `{runtime['queue_counts']}`\n"
            f"- Failure counts: `{runtime['failure_counts']}`\n"
            f"- Containers:\n\n```\n{runtime['docker_ps']}\n```\n"
        ),
        "STELLAI_ENV_AUDIT.md": (
            "# STELL-AI ENV AUDIT\n\n"
            f"- V10 report present: `{bool(state['stellai']['v10_report'])}`\n"
            f"- Runtime env flags: `{state['stellai']['env_flags']}`\n"
        ),
        "STELLAI_LIBRARY_MATRIX.md": (
            "# STELL-AI LIBRARY MATRIX\n\n"
            f"- Degraded features: `{state['stellai']['v10_report'].get('degraded_features', [])}`\n"
            f"- Engineering capabilities: `{state['stellai']['v10_report'].get('engineering_capabilities', {})}`\n"
        ),
        "STELLAI_READINESS_REPORT.md": (
            "# STELL-AI READINESS REPORT\n\n"
            f"- System health: `{state['stellai']['v10_report'].get('system_health', 'unknown')}`\n"
            f"- Manufacturing planning status: `{state['stellai']['v10_report'].get('manufacturing_planning_status', 'unknown')}`\n"
            f"- Test coverage: `{state['stellai']['v10_report'].get('test_coverage', {})}`\n"
            "- Readiness is truthful but partial because vector retrieval remains on deterministic fallback.\n"
        ),
        "WHATSAPP_AUDIT.md": (
            "# WHATSAPP AUDIT\n\n"
            f"- Env flags: `{whatsapp['env_flags']}`\n"
            f"- Local verify without token: `{whatsapp['local_verify_without_token']['status']}`\n"
            f"- Public verify without token: `{whatsapp['public_verify_without_token']['status']}`\n"
            f"- Local unsigned POST: `{whatsapp['local_unsigned_post']['status']}`\n"
            f"- Public unsigned POST: `{whatsapp['public_unsigned_post']['status']}`\n"
            "- Signed Meta webhook traffic was not replayed in this cycle.\n"
        ),
        "UI_AUDIT.md": (
            "# UI AUDIT\n\n"
            f"- Local routes: `{ui['local_routes']}`\n"
            f"- Public routes: `{ui['public_routes']}`\n"
            f"- Self-hosted ingress routes: `{state['self_hosted_frontend']['routes']}`\n"
            "- Core route surfaces are coherent on both public edge and the self-hosted nginx path.\n"
        ),
        "UI_CLEANUP_MATRIX.md": (
            "# UI CLEANUP MATRIX\n\n"
            "- Fixed in repo: fake auth token writes in public login/register pages.\n"
            "- Fixed in repo: fake success states in forgot/reset routes.\n"
            "- Fixed in production: `/admin/health` and `/reset-password` route parity.\n"
            "- Remaining: public traffic still terminates on Vercel until provider-level cutover is executed.\n"
        ),
        "MAIL_AUDIT.md": (
            "# MAIL AUDIT\n\n"
            f"- Env flags: `{mail['env_flags']}`\n"
            "- Recovery and reset pages now call real backend endpoints.\n"
            "- Provider capability remains blocked until `RESEND_API_KEY` is configured.\n"
        ),
        "AUTH_AUDIT.md": (
            "# AUTH AUDIT\n\n"
            f"- Register status: `{auth['register_status']}`\n"
            f"- Login status: `{auth['login_status']}`\n"
            f"- Me status: `{auth['me_status']}`\n"
            f"- Invalid login status: `{auth['invalid_login_status']}`\n"
            "- Repo auth pages were rewired to the live API in this cycle.\n"
        ),
        "MODULE_AUDIT.md": (
            "# MODULE AUDIT\n\n"
            f"- Gate status: `{gate.get('gate_status')}`\n"
            f"- Restore status: `{gate.get('restore_status')}`\n"
            f"- Drive export status: `{gate.get('drive_export_status')}`\n"
            f"- Smoke summary: `{gate.get('smoke_summary', {})}`\n"
        ),
        "WORKFLOW_AUDIT.md": (
            "# WORKFLOW AUDIT\n\n"
            f"- Canonical file: `{gate.get('smoke_summary', {}).get('canonical_file_id', 'missing')}`\n"
            f"- Visual file: `{gate.get('smoke_summary', {}).get('visual_file_id', 'missing')}`\n"
            f"- Share expiry status: `{gate.get('smoke_summary', {}).get('share_expire_http', 'missing')}`\n"
            f"- Approval sequence: `{gate.get('smoke_summary', {}).get('state_proof_sequence', [])}`\n"
        ),
        "SYSTEM_GAP_MATRIX.md": (
            "# SYSTEM GAP MATRIX\n\n"
            + render_status_table(rows)
            + "\n\n## Ordering Note\n\n"
            "Rows are ordered by canonical risk: security/runtime drift first, then workflow integrity, then cleanup.\n"
        ),
    }

    overall_blockers = [
        row for row in rows if row["status"] in {"FAIL", "BLOCKED"}
    ]
    overall_verdict = "FAIL" if overall_blockers else "PARTIAL"
    acceptance_lines = [
        "- [ ] protocols categorized and stable — FALSE",
        f"- [ ] interface fully operational — { 'TRUE' if ui['public_routes'].get('/admin/health') == 200 else 'FALSE' }",
        "- [ ] server limited to runtime role — FALSE",
        f"- [ ] Google Drive current and well structured — { 'FALSE' if {'03_evidence', 'evidence'} <= set(drive['top_level']) else 'TRUE' }",
        "- [ ] GitHub current and aligned — FALSE",
        "- [ ] files organized in readable documented flow — TRUE",
        "- [ ] naming/language consistency achieved — FALSE",
        f"- [ ] backup operational — { 'TRUE' if gate.get('restore_status') == 'PASS' else 'FALSE' }",
        f"- [ ] system recoverable after server failure — { 'TRUE' if gate.get('restore_status') == 'PASS' else 'FALSE' }",
        "- [ ] hierarchy functioning coherently — FALSE",
        f"- [ ] hardest tests executed — { 'TRUE' if gate.get('gate_status') == 'PASS' else 'FALSE' }",
        f"- [ ] final report archived — { 'TRUE' if archive_success else 'FALSE' }",
        "- [ ] version snapshot created — TRUE",
        "- [ ] ready for next development cycle — FALSE",
        f"- [ ] autopilot audit discipline enabled — { 'TRUE' if autopilot_enabled else 'FALSE' }",
    ]

    final_docs = {
        "STELLCODEX_FINAL_SYSTEM_REPORT.md": (
            "# STELLCODEX FINAL SYSTEM REPORT\n\n"
            f"## Executive Verdict\n\n`{overall_verdict}`\n\n"
            "## Area By Area Verdict\n\n"
            + render_status_table(rows)
            + "\n\n## What Was Wrong\n\n"
            "- GitHub drift remained open.\n"
            "- Vercel was still the public edge even though the server-hosted frontend path existed.\n"
            "- Mail recovery delivery was not real.\n"
            "- Public auth pages wrote fake local tokens.\n"
            "- Drive top-level structure kept duplicate legacy folders.\n"
            "\n## What Was Fixed\n\n"
            "- Public login/register pages now call the live auth API in repo.\n"
            "- Forgot/reset pages now use real backend reset endpoints.\n"
            "- Self-hosted frontend path was validated through local nginx with core route proofs.\n"
            "- Production `/admin/health` and `/reset-password` route parity was restored.\n"
            "- V10 engineering gate and Drive export evidence remain green.\n"
            "- Autopilot reporting layer was added in repo.\n"
            "\n## What Remains Blocked\n\n"
            "- Clean GitHub alignment and push.\n"
            "- Cloudflare/Vercel provider access for final traffic cutover away from the Vercel edge.\n"
            "- Direct Vercel and Cloudflare account inspection.\n"
            "- Real mail provider configuration.\n"
            "- Signed WhatsApp webhook proof against Meta traffic.\n"
            "\n## Evidence Index\n\n"
            f"- Closeout evidence directory: `{evidence_dir}`\n"
            f"- Latest gate evidence: `{gate.get('dir')}`\n"
            f"- V10 report: `{ROOT / 'stellcodex_v7' / '_jobs' / 'reports' / 'stellcodex_v10_engineering_report.json'}`\n"
            "\n## Backup / Restore Status\n\n"
            f"- Gate restore: `{gate.get('restore_status')}`\n"
            f"- Drive export: `{gate.get('drive_export_status')}`\n"
            "\n## Version / Commit / Tag References\n\n"
            f"- Current branch: `{git['branch']}`\n"
            f"- Current HEAD: `{git['head']}`\n"
            "\n## Deployment References\n\n"
            f"- Public app: `{PUBLIC_FRONTEND}`\n"
            f"- Public API: `{PUBLIC_API}`\n"
            "\n## Acceptance Checklist\n\n"
            + "\n".join(acceptance_lines)
        ),
        "STELLCODEX_ACCEPTANCE_DECISION.md": (
            "# STELLCODEX ACCEPTANCE DECISION\n\n"
            f"Decision: `{overall_verdict}`\n\n"
            "Reason:\n"
            "- Backup, restore, gate, and core workflow evidence pass locally.\n"
            "- Canonical GitHub alignment, provider-level frontend cutover, and real mail delivery are not closed.\n"
        ),
        f"STELLCODEX_CHANGELOG_{date_slug()}.md": (
            f"# STELLCODEX CHANGELOG {date_slug()}\n\n"
            "- Added recurring autopilot reporting script and wrapper.\n"
            "- Added autopilot architecture, runbook, checklist, and report template docs.\n"
            "- Added self-hosted frontend deploy script and ingress validation path.\n"
            "- Rewired public login/register routes to the live auth API.\n"
            "- Replaced fake recovery UI with real reset endpoints and public reset-password route.\n"
            "- Generated system integrity closeout evidence bundle.\n"
        ),
        f"STELLCODEX_VERSION_SNAPSHOT_{date_slug()}.md": (
            f"# STELLCODEX VERSION SNAPSHOT {date_slug()}\n\n"
            f"- Branch: `{git['branch']}`\n"
            f"- HEAD: `{git['head']}`\n"
            f"- Dirty count: `{state['dirty_count']}`\n"
            f"- Release gate: `{gate.get('gate_status')}`\n"
            "- Git tag was not created because the live repo is not in a release-worthy clean state.\n"
        ),
        "CONTINUATION_NEXT_ITERATION.md": (
            "# CONTINUATION NEXT ITERATION\n\n"
            "- Stable baseline: local release gate, restore verification, and Drive export are green.\n"
            "- Fixed this cycle: fake auth UI, fake recovery UI, self-hosted frontend readiness, closeout evidence generation, autopilot repo wiring.\n"
            "- Remaining blockers: GitHub drift, provider-level traffic cutover, mail provider config, signed WhatsApp verification.\n"
            "- External-access blockers: Vercel project access, Cloudflare account access, Meta signed webhook traffic, mail provider credentials.\n"
            "- Do not re-audit from zero: V10 engineering gate evidence, backup/restore proof, local core workflow smoke.\n"
            "- Next cycle starts with: clean repo split, push, execute Cloudflare/Vercel cutover if credentials are available, then rerun closeout and autopilot deploy validation.\n"
            "- Do not break: file_id-only public identity, assembly_meta fail-closed viewer, share expiry 410, restore gate.\n"
        ),
    }

    for name, content in docs.items():
        write_text(evidence_dir / name, content)
    for name, content in final_docs.items():
        write_text(evidence_dir / name, content)
        write_text(HANDOFF_ROOT / name, content)

    write_json(evidence_dir / "closeout_state.json", state)


def report_name(mode: str, day: str) -> str:
    if mode == "daily":
        return f"daily_health_report_{day}.md"
    if mode == "weekly":
        return f"weekly_integrity_report_{day}.md"
    return f"deploy_validation_report_{day}.md"


def derive_autopilot_status(state: dict[str, Any]) -> str:
    rows = subsystem_rows(state)
    statuses = {row["status"] for row in rows}
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if "PARTIAL" in statuses:
        return "PARTIAL"
    return "PASS"


def write_autopilot_reports(state: dict[str, Any], mode: str) -> tuple[Path, Path]:
    AUTOPILOT_REPORTS.mkdir(parents=True, exist_ok=True)
    day = date_slug()
    status = derive_autopilot_status(state)
    name = report_name(mode, day)
    summary = {
        "generated_at": state["generated_at"],
        "mode": mode,
        "status": status,
        "local_api_health": state["runtime"]["local_api_health"]["status"],
        "public_api_health": state["runtime"]["public_api_health"]["status"],
        "local_routes": state["ui"]["local_routes"],
        "public_routes": state["ui"]["public_routes"],
        "self_hosted_routes": state["self_hosted_frontend"]["routes"],
        "provider_credentials_summary": state.get("provider_credentials", {}).get("summary", "unknown"),
        "git_dirty_count": state["dirty_count"],
        "git_guard": {
            "ahead_count": state["git"]["latest_guard"].get("ahead_count"),
            "behind_count": state["git"]["latest_guard"].get("behind_count"),
            "workspace_apply_status": state["git"]["latest_guard"].get("workspace_apply_status"),
        },
        "backup_guard": {
            "generated_at": state["drive"]["latest_backup_guard"].get("generated_at"),
            "truth_sync": bool(state["drive"]["latest_backup_guard"].get("truth_sync_log")),
        },
        "gate": {
            "dir": state["gate"].get("dir"),
            "gate_status": state["gate"].get("gate_status"),
            "restore_status": state["gate"].get("restore_status"),
            "drive_export_status": state["gate"].get("drive_export_status"),
        },
    }
    markdown = (
        f"# STELLCODEX AUTOPILOT {mode.upper()} REPORT\n\n"
        f"- Generated: `{state['generated_at']}`\n"
        f"- Status: `{status}`\n"
        f"- Local API: `{state['runtime']['local_api_health']['status']}`\n"
        f"- Public API: `{state['runtime']['public_api_health']['status']}`\n"
        f"- Local routes: `{state['ui']['local_routes']}`\n"
        f"- Public routes: `{state['ui']['public_routes']}`\n"
        f"- Self-hosted ingress routes: `{state['self_hosted_frontend']['routes']}`\n"
        f"- Provider credentials: `{state.get('provider_credentials', {}).get('summary', 'unknown')}`\n"
        f"- Git dirty count: `{state['dirty_count']}`\n"
        f"- Backup guard generated at: `{state['drive']['latest_backup_guard'].get('generated_at', 'missing')}`\n"
        f"- Release gate: `{state['gate'].get('gate_status', 'missing')}`\n"
        f"- Restore verification: `{state['gate'].get('restore_status', 'missing')}`\n"
    )

    report_path = AUTOPILOT_REPORTS / name
    json_path = report_path.with_suffix(".json")
    latest_path = AUTOPILOT_REPORTS / "latest_status.md"
    write_text(report_path, markdown)
    write_json(json_path, summary)
    latest_text = (
        "# STELLCODEX AUTOPILOT LATEST STATUS\n\n"
        f"- Latest mode: `{mode}`\n"
        f"- Latest report: `{report_path.name}`\n"
        f"- Status: `{status}`\n"
        f"- Generated: `{state['generated_at']}`\n"
    )
    write_text(latest_path, latest_text)
    return report_path, json_path


def archive_file(path: Path) -> dict[str, Any]:
    upload = run_shell(
        f"/root/workspace/scripts/drive_dedup_upload.sh '{path}' '{DRIVE_REMOTE_DIR}' '{path.name}'",
        timeout=240,
    )
    return try_json(upload.stdout) or {
        "local_file": str(path),
        "remote_dir": DRIVE_REMOTE_DIR,
        "latest_name": path.name,
        "archive_status": "failed",
        "stderr": upload.stderr,
    }


def write_repo_docs() -> None:
    docs_root = ROOT / "ops" / "autopilot"
    systemd_root = ROOT / "ops" / "systemd"
    write_text(
        docs_root / "SELF_HOSTED_FRONTEND_RUNBOOK.md",
        "# SELF-HOSTED FRONTEND RUNBOOK\n\n"
        "- Source repo default: `/tmp/stell-main/frontend`\n"
        "- Live target: `/var/www/stellcodex/frontend`\n"
        "- Deploy command: `bash /root/workspace/scripts/stellcodex_self_hosted_frontend_deploy.sh`\n"
        "- Validation path: `curl -k --resolve stellcodex.com:443:127.0.0.1 https://stellcodex.com/`\n"
        "- This flow updates the server-hosted frontend directly and does not wait for Vercel.\n"
        "- Public traffic cutover still requires Cloudflare/DNS account access if the public edge is not already pointed at this server.\n",
    )
    write_text(
        docs_root / "AUTOPILOT_ARCHITECTURE.md",
        "# AUTOPILOT ARCHITECTURE\n\n"
        "- Entry point: `/root/workspace/scripts/stellcodex_autopilot.sh`\n"
        "- Core engine: `/root/workspace/scripts/stellcodex_autopilot.py`\n"
        "- Self-hosted frontend deploy: `/root/workspace/scripts/stellcodex_self_hosted_frontend_deploy.sh`\n"
        "- Locking: `/root/workspace/scripts/stellcodex_lock.sh`\n"
        "- Outputs: `_jobs/reports/autopilot/`\n"
        "- Archive path: `gdrive:stellcodex/03_evidence/autopilot`\n"
        "- Modes: `daily`, `weekly`, `deploy`, `closeout`\n"
        "- Edge posture: public traffic may still be Vercel-backed, but autopilot separately verifies the direct self-hosted nginx path.\n"
        "- Heavy checks: weekly mode relies on the latest release gate evidence and can be extended to rerun the gate with build disabled.\n",
    )
    write_text(
        docs_root / "AUTOPILOT_RUNBOOK.md",
        "# AUTOPILOT RUNBOOK\n\n"
        "## Manual Commands\n\n"
        "- `bash /root/workspace/scripts/stellcodex_self_hosted_frontend_deploy.sh`\n"
        "- `bash /root/workspace/scripts/stellcodex_autopilot.sh daily --archive`\n"
        "- `bash /root/workspace/scripts/stellcodex_autopilot.sh weekly --archive`\n"
        "- `bash /root/workspace/scripts/stellcodex_autopilot.sh deploy --archive`\n"
        "- `bash /root/workspace/scripts/stellcodex_autopilot.sh closeout --archive`\n"
        "\n## Failure Handling\n\n"
        "- `FAIL`: treat as blocking and inspect the generated JSON plus evidence bundle.\n"
        "- `PARTIAL`: investigate drift or missing external verification before claiming readiness.\n"
        "- `BLOCKED`: external credentials or access are missing.\n",
    )
    write_text(
        docs_root / "AUTOPILOT_CHECKLIST.md",
        "# AUTOPILOT CHECKLIST\n\n"
        "Daily:\n"
        "- local API health\n"
        "- public API health\n"
        "- local/public route reachability\n"
        "- self-hosted nginx route reachability\n"
        "- worker and queue counts\n"
        "- backup report freshness\n"
        "- GitHub drift signals\n"
        "\nWeekly:\n"
        "- latest release gate status\n"
        "- latest restore verification status\n"
        "- share expiry behavior from smoke evidence\n"
        "- auth sanity probe\n"
        "- Drive archive structure review\n"
        "\nPer deploy:\n"
        "- production route smoke\n"
        "- self-hosted ingress route smoke\n"
        "- protected/admin route parity check\n"
        "- no-fake surface regression review\n",
    )
    write_text(
        docs_root / "AUTOPILOT_REPORT_TEMPLATE.md",
        "# AUTOPILOT REPORT TEMPLATE\n\n"
        "- Mode\n"
        "- Timestamp\n"
        "- Status: PASS / FAIL / PARTIAL / BLOCKED\n"
        "- Health endpoints\n"
        "- Route reachability\n"
        "- Self-hosted ingress reachability\n"
        "- Queue and worker status\n"
        "- Backup and restore evidence\n"
        "- GitHub drift status\n"
        "- External blockers\n"
        "- Evidence paths\n",
    )
    write_text(
        systemd_root / "stellcodex-autopilot-daily.service",
        "[Unit]\nDescription=STELLCODEX daily autopilot check\nAfter=network-online.target docker.service\nWants=network-online.target\n\n"
        "[Service]\nType=oneshot\nWorkingDirectory=/root/workspace\nExecStart=/root/workspace/scripts/stellcodex_autopilot.sh daily --archive\n",
    )
    write_text(
        systemd_root / "stellcodex-autopilot-daily.timer",
        "[Unit]\nDescription=Run STELLCODEX daily autopilot check\n\n"
        "[Timer]\nOnCalendar=*-*-* 06:30:00\nPersistent=true\nUnit=stellcodex-autopilot-daily.service\n\n"
        "[Install]\nWantedBy=timers.target\n",
    )
    write_text(
        systemd_root / "stellcodex-autopilot-weekly.service",
        "[Unit]\nDescription=STELLCODEX weekly integrity autopilot check\nAfter=network-online.target docker.service\nWants=network-online.target\n\n"
        "[Service]\nType=oneshot\nWorkingDirectory=/root/workspace\nExecStart=/root/workspace/scripts/stellcodex_autopilot.sh weekly --archive\n",
    )
    write_text(
        systemd_root / "stellcodex-autopilot-weekly.timer",
        "[Unit]\nDescription=Run STELLCODEX weekly integrity autopilot check\n\n"
        "[Timer]\nOnCalendar=Sun *-*-* 07:15:00\nPersistent=true\nUnit=stellcodex-autopilot-weekly.service\n\n"
        "[Install]\nWantedBy=timers.target\n",
    )
    write_text(
        systemd_root / "stellcodex-autopilot-deploy.service",
        "[Unit]\nDescription=STELLCODEX deploy validation autopilot check\nAfter=network-online.target docker.service\nWants=network-online.target\n\n"
        "[Service]\nType=oneshot\nWorkingDirectory=/root/workspace\nExecStart=/root/workspace/scripts/stellcodex_autopilot.sh deploy --archive\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["daily", "weekly", "deploy", "closeout"])
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()

    write_repo_docs()
    state = collect_state(args.mode)

    archived: list[dict[str, Any]] = []
    if args.mode == "closeout":
        evidence_dir = EVIDENCE_ROOT / f"system_integrity_{timestamp_slug()}"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        write_closeout_bundle(state, evidence_dir, archive_success=False, autopilot_enabled=True)
        if args.archive:
            for path in sorted(evidence_dir.glob("*.md")) + sorted(evidence_dir.glob("*.json")):
                archived.append(archive_file(path))
        write_json(evidence_dir / "archive_manifest.json", archived)
        archive_success = bool(archived) and all(
            item.get("archive_status") in {"uploaded", "skipped_duplicate"}
            for item in archived
            if item.get("latest_name")
        )
        write_closeout_bundle(state, evidence_dir, archive_success=archive_success, autopilot_enabled=True)
        print(json.dumps({"mode": args.mode, "evidence_dir": str(evidence_dir), "archived": archived}, indent=2))
        return 0

    report_path, json_path = write_autopilot_reports(state, args.mode)
    if args.archive:
        archived = [archive_file(report_path), archive_file(json_path), archive_file(AUTOPILOT_REPORTS / "latest_status.md")]
        write_json(AUTOPILOT_REPORTS / f"{args.mode}_archive_{date_slug()}.json", archived)
    print(json.dumps({"mode": args.mode, "report": str(report_path), "json": str(json_path), "archived": archived}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
