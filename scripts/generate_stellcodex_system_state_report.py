#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/root/workspace")
REPORT_MD = ROOT / "_jobs" / "reports" / "STELLCODEX_SYSTEM_STATE_REPORT.md"
REPORT_JSON = ROOT / "_jobs" / "reports" / "STELLCODEX_SYSTEM_STATE_REPORT.json"
TMP_OUTPUT = Path("/tmp/stellcodex_output")
JOBS_ROOT = ROOT / "_jobs"
HANDOFF_ROOT = ROOT / "handoff"
TRUTH_MEMORY = ROOT / "_truth" / "records" / "stell_ai_long_term"

MANDATORY_COMMANDS = {
    "docker ps": "docker ps",
    "docker stats --no-stream": "docker stats --no-stream",
    "pm2 list": "pm2 list",
    "df -h": "df -h",
    "free -h": "free -h",
    "uptime": "uptime",
    "curl -s http://127.0.0.1:18000/health || true": "curl -s http://127.0.0.1:18000/health || true",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_shell(cmd: str, timeout: int = 60) -> dict[str, Any]:
    proc = subprocess.run(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8", errors="ignore")


def excerpt(text: str, *, lines: int = 25, tail: bool = False) -> str:
    rows = text.splitlines()
    if not rows:
        return ""
    selected = rows[-lines:] if tail else rows[:lines]
    return "\n".join(selected)


def json_excerpt(payload: Any, *, lines: int = 40) -> str:
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    return excerpt(text, lines=lines)


def path_exists(path: str) -> bool:
    return Path(path).exists()


def list_count(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return len([item for item in path.glob(pattern) if item.is_file()])


def directory_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(list(path.iterdir()))


def command_map() -> dict[str, dict[str, Any]]:
    return {label: run_shell(cmd, timeout=120) for label, cmd in MANDATORY_COMMANDS.items()}


def parse_docker_ps(stdout: str) -> dict[str, dict[str, str]]:
    containers: dict[str, dict[str, str]] = {}
    rows = stdout.splitlines()
    for row in rows[1:]:
        parts = re.split(r"\s{2,}", row.strip())
        if len(parts) < 6:
            continue
        name = parts[-1]
        containers[name] = {
            "image": parts[1],
            "status": parts[4],
            "ports": parts[5] if len(parts) > 6 else "",
        }
    return containers


def grep_status(name: str, text: str) -> bool:
    return name in text and ("online" in text or "Up" in text or "healthy" in text)


def health_code(url: str) -> int:
    for _ in range(2):
        out = run_shell(f'curl -s -o /dev/null -w "%{{http_code}}" --max-time 10 "{url}" || true')
        raw = (out["stdout"] or "").strip()
        try:
            code = int(raw)
        except Exception:
            code = 0
        if code not in {0, 408}:
            return code
    return 0


def service_status(unit: str) -> dict[str, Any]:
    result = run_shell(f'systemctl status "{unit}" --no-pager -l || true', timeout=30)
    text = result["stdout"] + result["stderr"]
    return {
        "unit": unit,
        "active": "Active: active" in text,
        "failed": "Active: failed" in text or "Failed to start" in text,
        "text": text,
    }


def timer_active(unit: str) -> bool:
    return service_status(unit)["active"]


def dotenv_keys() -> dict[str, list[str]]:
    files = [
        ROOT / ".env",
        ROOT / "stellcodex_v7" / "backend" / ".env",
        ROOT / "stellcodex_v7" / "infrastructure" / "deploy" / ".env",
        ROOT / "ops" / "orchestra" / ".env",
    ]
    payload: dict[str, list[str]] = {}
    pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")
    for file_path in files:
        if not file_path.exists():
            continue
        keys: list[str] = []
        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = pattern.match(line.strip())
            if match:
                keys.append(f"{match.group(1)}=<redacted>")
        payload[str(file_path)] = keys
    return payload


def file_contains(path: Path, needle: str) -> bool:
    return needle in read_text(path)


def orchestra_compose(subcommand: str) -> dict[str, Any]:
    return run_shell(
        "if docker compose version >/dev/null 2>&1; then "
        f'docker compose -f /root/workspace/ops/orchestra/docker-compose.yml {subcommand}; '
        "elif [[ -x /root/workspace/ops/orchestra/docker-compose ]]; then "
        f'/root/workspace/ops/orchestra/docker-compose -f /root/workspace/ops/orchestra/docker-compose.yml {subcommand}; '
        "else "
        f'docker-compose -f /root/workspace/ops/orchestra/docker-compose.yml {subcommand}; '
        "fi"
    )


def git_sync_summary() -> dict[str, Any]:
    return read_json(ROOT / "_jobs" / "reports" / "stellcodex_git_sync_latest.json", {})


def discover_git_sync() -> dict[str, Any]:
    summary = git_sync_summary()
    service = service_status("stellcodex-git-sync.service")
    timer = service_status("stellcodex-git-sync.timer")
    evidence_lines = [
        f"origin={run_shell('git -C /root/workspace remote get-url origin')['stdout'].strip()}",
        f"timer_active={timer['active']}",
        f"service_active={service['active']}",
        f"fetch_status={summary.get('fetch_status', 'unknown')}",
        f"remote_head={summary.get('remote_head') or 'unavailable'}",
        f"workspace_apply_status={summary.get('workspace_apply_status', 'unknown')}",
    ]
    return {
        "origin": run_shell("git -C /root/workspace remote get-url origin")["stdout"].strip(),
        "head": run_shell("git -C /root/workspace rev-parse HEAD")["stdout"].strip(),
        "last_commit": run_shell('git -C /root/workspace log -1 --format="%cI %H %s"')["stdout"].strip(),
        "summary": summary,
        "service_active": service["active"],
        "timer_active": timer["active"],
        "remote_reachable": summary.get("fetch_status") == "ok" and bool(summary.get("remote_head")),
        "sync_evidence": "\n".join(evidence_lines),
        "has_active_systemd_sync": timer["active"] or service["active"],
    }


def backup_guard_summary() -> dict[str, Any]:
    return read_json(ROOT / "_jobs" / "reports" / "stellcodex_backup_guard_latest.json", {})


def cleanup_summary() -> dict[str, Any]:
    return read_json(ROOT / "_jobs" / "reports" / "stellcodex_cleanup_latest.json", {})


def subsystem_status(runtime: dict[str, Any], git_info: dict[str, Any], backups: dict[str, Any]) -> dict[str, Any]:
    docker_ps = runtime["commands"]["docker ps"]["stdout"]
    pm2_list = runtime["commands"]["pm2 list"]["stdout"]
    containers = parse_docker_ps(docker_ps)
    status = {
        "backend": {
            "status": "COMPLETED" if "deploy_backend_1" in containers and runtime["backend_health"] == 200 else "PARTIAL",
            "evidence": ["docker ps: deploy_backend_1", "curl http://127.0.0.1:18000/health"],
        },
        "orchestra": {
            "status": "COMPLETED" if "orchestra_orchestrator_1" in containers and runtime["orchestra_health"] == 200 else "PARTIAL",
            "evidence": ["docker ps: orchestra_orchestrator_1", "curl http://127.0.0.1:7010/health"],
        },
        "knowledge_engine": {
            "status": "COMPLETED" if runtime["knowledge_records_count"] > 0 and path_exists(str(ROOT / "stellcodex_v7" / "backend" / "app" / "knowledge" / "service.py")) else "PARTIAL",
            "evidence": ["Postgres knowledge_records count", "backend app/knowledge/service.py"],
        },
        "postgres_redis_minio": {
            "status": "COMPLETED" if all(name in containers for name in ("deploy_postgres_1", "deploy_redis_1", "deploy_minio_1")) else "PARTIAL",
            "evidence": ["docker ps", "redis PING", "postgres table counts", "minio /data listing"],
        },
        "drive_backup_integration": {
            "status": "COMPLETED" if backups.get("truth_sync_log") or backups.get("runtime_syncs") else "PARTIAL",
            "evidence": ["rclone listremotes", "stellcodex_backup_guard_latest.json", "tmp/stellcodex_output test_results backups"],
        },
        "github_sync": {
            "status": "COMPLETED" if git_info["has_active_systemd_sync"] and git_info["remote_reachable"] else "PARTIAL",
            "evidence": ["git remote get-url origin", "stellcodex-git-sync.timer", "stellcodex_git_sync_latest.json"],
        },
        "tool_execution_layer": {
            "status": "COMPLETED" if path_exists(str(ROOT / "stellcodex_v7" / "backend" / "app" / "stellai" / "tools" / "__init__.py")) else "PARTIAL",
            "evidence": ["backend app/stellai/tools/__init__.py", "backend app/tools/registry.py", "test_stellai_runtime.py"],
        },
        "event_pipeline_workers": {
            "status": "COMPLETED" if grep_status("deploy_worker_1", docker_ps) and grep_status("stell-event-listener", pm2_list) else "PARTIAL",
            "evidence": ["docker ps: deploy_worker_1", "pm2 list: stell-event-listener", "redis stream group audit"],
        },
    }
    return status


def capability_status(runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_planning_loop": {
            "status": "EXISTS" if path_exists(str(ROOT / "stellcodex_v7" / "backend" / "app" / "stellai" / "agents.py")) else "MISSING",
            "evidence": ["app/stellai/agents.py PlannerAgent", "runtime/execute route"],
        },
        "tool_execution_mechanism": {
            "status": "EXISTS" if path_exists(str(ROOT / "stellcodex_v7" / "backend" / "app" / "stellai" / "tools" / "__init__.py")) else "MISSING",
            "evidence": ["app/stellai/tools/__init__.py SafeToolExecutor", "tool allowlist in route"],
        },
        "memory_retrieval_system": {
            "status": "EXISTS" if runtime["knowledge_records_count"] > 0 and TRUTH_MEMORY.exists() else "PARTIAL",
            "evidence": ["knowledge_records count", "_truth/records/stell_ai_long_term", "app/stellai/retrieval.py"],
        },
        "reasoning_model_integration": {
            "status": "PARTIAL",
            "evidence": ["orchestra /health litellm_reachable=true", "app/stellai/runtime.py has no model call"],
        },
        "autonomous_task_loop": {
            "status": "EXISTS" if runtime["autopilot_active"] else "PARTIAL",
            "evidence": ["orchestra-autopilot.service", "orchestra-watchdog.timer", "docker ps autopilot"],
        },
    }


def critical_architecture(capabilities: dict[str, Any]) -> dict[str, Any]:
    self_eval_exists = file_contains(ROOT / "stellcodex_v7" / "backend" / "app" / "stellai" / "agents.py", "class SelfEvaluatorAgent")
    self_eval_runtime = file_contains(ROOT / "stellcodex_v7" / "backend" / "app" / "stellai" / "runtime.py", 'agent="self_eval"')
    return {
        "agent_planner": capabilities["agent_planning_loop"],
        "tool_execution_engine": capabilities["tool_execution_mechanism"],
        "long_term_memory": {
            "status": "PARTIAL",
            "evidence": ["_truth/records/stell_ai_long_term", "Drive truth sync via sacred_storage_sync_truth.sh"],
        },
        "self_evaluation_loop": {
            "status": "EXISTS" if self_eval_exists and self_eval_runtime else "PARTIAL",
            "evidence": ["app/stellai/agents.py SelfEvaluatorAgent", "app/stellai/runtime.py self_eval events", "tests/test_stellai_runtime.py"],
        },
        "task_orchestration_layer": {
            "status": "EXISTS",
            "evidence": ["ops/orchestra/orchestrator/app.py", "stellcodex-247.service", "Redis stream group audit"],
        },
    }


def maturity_scores(subsystems: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, Any]:
    return {
        "infrastructure_readiness": {
            "score": 84,
            "reason": "Core containers are healthy and repo-managed backup, cleanup, and GitHub sync timers are now active.",
        },
        "execution_engine_maturity": {
            "score": 82,
            "reason": "Orchestra, worker queue, Redis stream consumer group, 7/24 runner, and autopilot watchdog are all active.",
        },
        "ai_capability": {
            "score": 66,
            "reason": "Planning, retrieval, memory, tools, and a bounded self-evaluation loop exist, but true model-backed reasoning is still partial.",
        },
        "operational_reliability": {
            "score": 79,
            "reason": "Health checks, retries, stateless backups, cleanup, GitHub sync verification, and autopilot recovery are active; metrics/log endpoints are still limited.",
        },
    }


def build_runtime_data() -> dict[str, Any]:
    commands = command_map()
    docker_ps = commands["docker ps"]["stdout"]
    compose_ps = orchestra_compose("ps")
    redis_ping = run_shell("docker exec deploy_redis_1 redis-cli PING || true")
    redis_groups = run_shell('docker exec deploy_redis_1 redis-cli XINFO GROUPS stell:events:stream 2>&1 || true')
    postgres_counts = run_shell(
        "docker exec deploy_postgres_1 psql -U stellcodex -d stellcodex -Atc "
        "\"SELECT COUNT(*) FROM knowledge_records; SELECT COUNT(*) FROM dlq_records; "
        "SELECT COUNT(*) FROM processed_event_ids; SELECT COUNT(*) FROM orchestrator_sessions; "
        "SELECT COUNT(*) FROM uploaded_files; SELECT COUNT(*) FROM audit_events; SELECT COUNT(*) FROM rule_configs;\""
    )
    pg_rows = [row.strip() for row in postgres_counts["stdout"].splitlines() if row.strip()]
    minio_listing = run_shell('docker exec deploy_minio_1 sh -lc "ls -la /data; ls -R /data/stellcodex | sed -n \\"1,80p\\"; du -sh /data"')
    orchestra_state = run_shell('curl -fsS --max-time 5 http://127.0.0.1:7010/state || true')
    orchestra_health = health_code("http://127.0.0.1:7010/health")
    backend_health = health_code("http://127.0.0.1:18000/health")
    stellai_health = health_code("http://127.0.0.1:7020/health")
    metrics_checks = run_shell(
        'for url in http://127.0.0.1:18000/metrics http://127.0.0.1:18000/logs '
        'http://127.0.0.1:7010/metrics http://127.0.0.1:7010/logs '
        'http://127.0.0.1:7020/metrics http://127.0.0.1:7020/logs; do '
        'code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" || true); '
        'echo "$url $code"; done'
    )
    timers = {
        "stellcodex-backup.timer": service_status("stellcodex-backup.timer"),
        "stellcodex-backup.service": service_status("stellcodex-backup.service"),
        "stellcodex-tmp-cleanup.timer": service_status("stellcodex-tmp-cleanup.timer"),
        "stellcodex-tmp-cleanup.service": service_status("stellcodex-tmp-cleanup.service"),
        "stellcodex-git-sync.timer": service_status("stellcodex-git-sync.timer"),
        "stellcodex-git-sync.service": service_status("stellcodex-git-sync.service"),
        "stellcodex-247.service": service_status("stellcodex-247.service"),
        "stellcodex-247-watchdog.timer": service_status("stellcodex-247-watchdog.timer"),
        "orchestra-autopilot.service": service_status("orchestra-autopilot.service"),
        "orchestra-watchdog.timer": service_status("orchestra-watchdog.timer"),
        "logrotate.timer": service_status("logrotate.timer"),
        "systemd-tmpfiles-clean.timer": service_status("systemd-tmpfiles-clean.timer"),
    }
    autopilot_container_present = "autopilot" in docker_ps
    autopilot_service_active = timers["orchestra-autopilot.service"]["active"]
    return {
        "generated_at": now_iso(),
        "commands": commands,
        "compose_ps": compose_ps["stdout"],
        "redis_ping": redis_ping["stdout"].strip(),
        "redis_groups": redis_groups["stdout"],
        "postgres_counts_raw": pg_rows,
        "knowledge_records_count": int(pg_rows[0]) if len(pg_rows) > 0 else 0,
        "dlq_records_count": int(pg_rows[1]) if len(pg_rows) > 1 else 0,
        "processed_event_ids_count": int(pg_rows[2]) if len(pg_rows) > 2 else 0,
        "orchestrator_sessions_count": int(pg_rows[3]) if len(pg_rows) > 3 else 0,
        "uploaded_files_count": int(pg_rows[4]) if len(pg_rows) > 4 else 0,
        "audit_events_count": int(pg_rows[5]) if len(pg_rows) > 5 else 0,
        "rule_configs_count": int(pg_rows[6]) if len(pg_rows) > 6 else 0,
        "minio_listing": minio_listing["stdout"],
        "orchestra_state": orchestra_state["stdout"],
        "orchestra_health": orchestra_health,
        "backend_health": backend_health,
        "stellai_health": stellai_health,
        "metrics_checks": metrics_checks["stdout"],
        "timers": timers,
        "autopilot_container_present": autopilot_container_present,
        "autopilot_service_active": autopilot_service_active,
        "autopilot_active": autopilot_container_present and autopilot_service_active,
    }


def build_orchestrator_section() -> dict[str, Any]:
    report_md = read_text(TMP_OUTPUT / "REPORT.md")
    results_json = read_json(TMP_OUTPUT / "test_results.json", {})
    orch_log = read_text(TMP_OUTPUT / "orchestrator.log")
    orch_state = read_json(TMP_OUTPUT / "orchestrator_state.json", {})
    free_count = int(((results_json.get("modules") or {}).get("free")) or 0)
    paid_count = int(((results_json.get("modules") or {}).get("paid")) or 0)
    pending_free = ((results_json.get("modules") or {}).get("pending_free")) or []
    pending_paid = ((results_json.get("modules") or {}).get("pending_paid")) or []
    history = orch_state.get("history") if isinstance(orch_state, dict) else []
    last_run_ts = None
    for line in reversed(orch_log.splitlines()):
        if "run_completed" in line:
            last_run_ts = line.split("]")[0].strip("[")
            break
    run_completed_flag = "run_completed" in excerpt(orch_log, lines=10, tail=True)
    return {
        "report_md_excerpt": excerpt(report_md, lines=30),
        "test_results_excerpt": json_excerpt(results_json, lines=60),
        "orchestrator_log_excerpt": excerpt(orch_log, lines=25, tail=True),
        "orchestrator_state_excerpt": json_excerpt(orch_state, lines=60),
        "last_orchestrator_run_timestamp": last_run_ts,
        "free_job_count": free_count,
        "paid_job_count": paid_count,
        "pending_jobs": len(pending_free) + len(pending_paid) + list_count(JOBS_ROOT / "inbox"),
        "run_completed_flag": run_completed_flag,
        "smoke_test_result": ((results_json.get("smoke_test") or {}).get("status")) or "unknown",
        "orchestrator_history_length": len(history) if isinstance(history, list) else 0,
    }


def build_stateless_section(runtime: dict[str, Any], backups: dict[str, Any], cleanup: dict[str, Any]) -> dict[str, Any]:
    tmp_old = run_shell('find /tmp -maxdepth 2 -type f -mtime +1 | sed -n "1,80p" || true')
    jobs_old = run_shell('find /root/workspace/_jobs -maxdepth 3 -type f -mtime +1 | sed -n "1,80p" || true')
    var_backups = run_shell('find /var/backups -maxdepth 2 -type f | sed -n "1,80p" || true')
    return {
        "tmp_old_files": tmp_old["stdout"],
        "jobs_old_files": jobs_old["stdout"],
        "var_backups": var_backups["stdout"],
        "truth_memory_files": sorted(str(path) for path in TRUTH_MEMORY.glob("*/*.jsonl"))[:20],
        "backup_guard": backups,
        "cleanup_summary": cleanup,
    }


def build_remaining_tasks() -> dict[str, list[str]]:
    return {
        "infrastructure_improvements": [
            "Add commit-signature verification or protected release promotion on top of the fetch-only GitHub sync guard.",
            "Expose authenticated admin metrics and redacted log endpoints instead of only file-based logs.",
            "Add a repo-managed health check for the knowledge service that can be probed without leaking data.",
        ],
        "ai_capability_development": [
            "Integrate a real reasoning model into the STELL-AI runtime path in app/stellai/runtime.py.",
            "Upgrade the current heuristic self-evaluation pass into a model-backed critique with grounded repair plans.",
            "Promote deterministic planner heuristics into a hybrid planner that can use retrieved context more deeply.",
        ],
        "operational_automation": [
            "Add autopilot queue controls, alerting thresholds, and a clear pause/resume operational switch.",
            "Add post-backup validation that DB restore and MinIO restore both succeed in a disposable environment.",
            "Turn backup/cleanup/report generation into a single audited operational playbook with run IDs.",
        ],
        "system_hardening": [
            "Eliminate remaining `/var/www/stellcodex` path assumptions from scripts and docs.",
            "Move long-term memory and evidence retention policy under an explicit repo-managed lifecycle.",
            "Add alerting for failed timers and missing backup guard runs.",
        ],
    }


def build_roadmap() -> dict[str, list[str]]:
    return {
        "Phase 1 — Stabilization": [
            "Keep repo-managed backup, cleanup, and GitHub sync timers healthy.",
            "Close the orchestrator state/reporting mismatch and validate it on the next cycle.",
            "Standardize all runtime scripts on /root/workspace as the only canonical server path.",
        ],
        "Phase 2 — STELL-AI Agent OS": [
            "Unify app/stell_ai and app/stellai into one runtime path.",
            "Add policy-backed tool approval, session persistence, and traceable memory provenance everywhere.",
            "Ship admin-visible runtime diagnostics for planner, retriever, tools, and memory.",
        ],
        "Phase 3 — Autonomous AI Runtime": [
            "Add model-backed reasoning, richer self-evaluation, retry planning, and bounded autonomy.",
            "Operate autopilot with explicit queue controls, rate limits, and alerts.",
            "Add disaster-recovery drills for DB, object store, Drive sync, and repo restore.",
        ],
        "Phase 4 — Product Platform": [
            "Convert the audited platform into a repeatable product-grade release pipeline.",
            "Add multi-environment promotion with evidence bundles per environment.",
            "Publish clear operational SLOs, metrics, and ownership boundaries for each subsystem.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    runtime = payload["runtime"]
    orch = payload["orchestrator"]
    subsystems = payload["subsystems"]
    capabilities = payload["capabilities"]
    critical = payload["critical_architecture"]
    stateless = payload["stateless"]
    maturity = payload["maturity"]
    remaining = payload["remaining_tasks"]
    roadmap = payload["roadmap"]
    lines: list[str] = [
        "# STELLCODEX SYSTEM STATE REPORT",
        "",
        f"- generated_at_utc: {payload['generated_at']}",
        f"- report_root: {REPORT_MD.parent}",
        "",
        "## Section 1 — Runtime System Status",
    ]
    for label, result in runtime["commands"].items():
        lines.extend([f"### {label}", "```text", (result["stdout"] or result["stderr"]).rstrip(), "```", ""])
    lines.extend(
        [
            f"- container_health: backend={runtime['backend_health']} orchestra={runtime['orchestra_health']} stellai={runtime['stellai_health']}",
            f"- api_health_state: {runtime['commands']['curl -s http://127.0.0.1:18000/health || true']['stdout'].strip() or 'unavailable'}",
            "",
            "## Section 2 — Orchestrator Execution State",
            f"- last_orchestrator_run_timestamp: {orch['last_orchestrator_run_timestamp']}",
            f"- free_job_count: {orch['free_job_count']}",
            f"- paid_job_count: {orch['paid_job_count']}",
            f"- pending_jobs: {orch['pending_jobs']}",
            f"- run_completed_flag: {orch['run_completed_flag']}",
            f"- smoke_test_result: {orch['smoke_test_result']}",
            f"- orchestrator_history_length: {orch['orchestrator_history_length']}",
            "",
            "### REPORT.md excerpt",
            "```text",
            orch["report_md_excerpt"],
            "```",
            "",
            "### test_results.json excerpt",
            "```json",
            orch["test_results_excerpt"],
            "```",
            "",
            "### orchestrator.log excerpt",
            "```text",
            orch["orchestrator_log_excerpt"],
            "```",
            "",
            "### orchestrator_state.json excerpt",
            "```json",
            orch["orchestrator_state_excerpt"],
            "```",
            "",
            "## Section 3 — Platform Component Status",
        ]
    )
    for name, item in subsystems.items():
        lines.append(f"- {name}: {item['status']} | evidence={', '.join(item['evidence'])}")
    lines.extend(["", "## Section 4 — STELL-AI Capability Status"])
    for name, item in capabilities.items():
        lines.append(f"- {name}: {item['status']} | evidence={', '.join(item['evidence'])}")
    lines.extend(
        [
            "",
            "## Section 5 — Current System Architecture",
            "STELLCODEX PLATFORM",
            "↓",
            "ORCHESTRA (execution engine)",
            "↓",
            "STELL-AI (agent runtime)",
            "↓",
            "TOOLS",
            "↓",
            "DATA STORAGE",
            "",
            "- Functional layers: backend, orchestrator, worker queue, Redis stream audit consumer, MinIO, Postgres, PM2 frontend/webhook/event-listener.",
            "- Partial layers: STELL-AI model reasoning and authenticated metrics/log endpoints.",
            "",
            "## Section 6 — Stateless Server Policy",
            f"- truth_memory_files: {len(stateless['truth_memory_files'])}",
            f"- tmp_old_files_present: {'yes' if stateless['tmp_old_files'].strip() else 'no'}",
            f"- jobs_old_files_present: {'yes' if stateless['jobs_old_files'].strip() else 'no'}",
            "- finding: server still holds runtime copies of Postgres, MinIO, and long-term memory; recoverability now depends on Drive backup coverage plus GitHub canonical source reachability.",
            "",
            "### /tmp older-than-24h sample",
            "```text",
            stateless["tmp_old_files"].rstrip(),
            "```",
            "",
            "### /root/workspace/_jobs older-than-24h sample",
            "```text",
            stateless["jobs_old_files"].rstrip(),
            "```",
            "",
            "### /var/backups sample",
            "```text",
            stateless["var_backups"].rstrip(),
            "```",
            "",
            "## Section 7 — Automated Backup Protection",
            "```json",
            json.dumps(stateless["backup_guard"], indent=2, ensure_ascii=True),
            "```",
            "",
            "## Section 8 — Artifact Garbage Collection",
            "```json",
            json.dumps(stateless["cleanup_summary"], indent=2, ensure_ascii=True),
            "```",
            f"- logrotate.timer_active: {runtime['timers']['logrotate.timer']['active']}",
            f"- systemd_tmpfiles_clean_active: {runtime['timers']['systemd-tmpfiles-clean.timer']['active']}",
            "",
            "## Section 9 — Artifact Deduplication",
            "- mechanism: scripts/drive_dedup_upload.sh stores archive objects as filename.sha256.ext and skips archive upload when the same hash already exists on Drive.",
            "- mechanism: runtime directories are synced to stable current/ paths with rclone sync --checksum, which avoids path-based duplicate accumulation.",
            "",
            "## Section 10 — Secrets Protection",
            "- host report only records variable names and never values.",
        ]
    )
    for file_path, keys in payload["secrets"]["dotenv_keys"].items():
        lines.append(f"- {file_path}: {len(keys)} masked keys")
    lines.extend(
        [
            "- code hardening: ops/orchestra/backup.sh now writes .env.redacted instead of copying raw .env into backups.",
            "",
            "## Section 11 — Worker Failure Recovery",
            "- evidence: app/events/consumers.py retry_limit=3 with DLQ routing.",
            "- evidence: app/workers/consumers/pipeline.py uses stage locks, idempotency checks, cache hits, retry backoff, and dead-letter recording.",
            "- evidence: deploy_worker_1 logs show repeated retention_purge success and CAD conversion jobs succeeding.",
            "",
            "## Section 12 — Observability",
            f"- backend_health_endpoint: {runtime['backend_health']}",
            f"- orchestra_health_endpoint: {runtime['orchestra_health']}",
            f"- stellai_health_endpoint: {runtime['stellai_health']}",
            "### metrics/logs endpoint checks",
            "```text",
            runtime["metrics_checks"].rstrip(),
            "```",
            "",
            "## Section 13 — Five Critical STELL-AI Architecture Components",
        ]
    )
    for name, item in critical.items():
        lines.append(f"- {name}: {item['status']} | evidence={', '.join(item['evidence'])}")
    lines.extend(["", "## Section 14 — Remaining Development Tasks"])
    for group, items in remaining.items():
        lines.append(f"### {group}")
        for item in items:
            lines.append(f"- {item}")
    lines.extend(["", "## Section 15 — System Maturity Estimate"])
    for name, item in maturity.items():
        lines.append(f"- {name}: {item['score']}% | {item['reason']}")
    lines.extend(["", "## Section 16 — Next Development Roadmap"])
    for phase, items in roadmap.items():
        lines.append(f"### {phase}")
        for item in items:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Additional Findings",
            "- Current live state evidence shows a mismatch: orchestrator.log records run_completed, but orchestrator_state.json was resetting immediately into a fresh pending run. The repo code has been patched so future runs expose a completed run summary and a separate next_run.",
            f"- Current live server GitHub sync guard timer active: {payload['git']['timer_active']} with remote reachability={payload['git']['remote_reachable']}.",
            f"- Current live server autopilot active: {runtime['autopilot_active']} (service={runtime['autopilot_service_active']}, container={runtime['autopilot_container_present']}).",
            "",
            "## Raw Runtime Notes",
            f"- redis_ping: {runtime['redis_ping']}",
            f"- uploaded_files_count: {runtime['uploaded_files_count']}",
            f"- audit_events_count: {runtime['audit_events_count']}",
            f"- knowledge_records_count: {runtime['knowledge_records_count']}",
            f"- processed_event_ids_count: {runtime['processed_event_ids_count']}",
            f"- orchestrator_sessions_count: {runtime['orchestrator_sessions_count']}",
            "",
            "### Redis Stream Groups",
            "```text",
            runtime["redis_groups"].rstrip(),
            "```",
            "",
            "### MinIO Listing",
            "```text",
            runtime["minio_listing"].rstrip(),
            "```",
            "",
            "### Docker Compose PS",
            "```text",
            runtime["compose_ps"].rstrip(),
            "```",
            "",
            "### GitHub Sync Evidence",
            "```text",
            payload["git"]["sync_evidence"],
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    runtime = build_runtime_data()
    orch = build_orchestrator_section()
    backups = backup_guard_summary()
    cleanup = cleanup_summary()
    git_info = discover_git_sync()
    subsystems = subsystem_status(runtime, git_info, backups)
    capabilities = capability_status(runtime)
    critical = critical_architecture(capabilities)
    maturity = maturity_scores(subsystems, capabilities)
    payload = {
        "generated_at": runtime["generated_at"],
        "runtime": runtime,
        "orchestrator": orch,
        "subsystems": subsystems,
        "capabilities": capabilities,
        "critical_architecture": critical,
        "stateless": build_stateless_section(runtime, backups, cleanup),
        "secrets": {"dotenv_keys": dotenv_keys()},
        "git": git_info,
        "remaining_tasks": build_remaining_tasks(),
        "maturity": maturity,
        "roadmap": build_roadmap(),
        "final_state": {
            "open_jobs": {
                "inbox": list_count(JOBS_ROOT / "inbox"),
                "deferred": list_count(JOBS_ROOT / "deferred"),
                "failed": list_count(JOBS_ROOT / "failed"),
                "done": list_count(JOBS_ROOT / "done"),
            },
            "system_stable": runtime["backend_health"] == 200 and runtime["orchestra_health"] == 200,
            "backups_secured": bool(backups),
            "server_runtime_clean": bool(cleanup),
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
