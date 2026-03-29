from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg2

RUNS_DIR = Path("/root/workspace/_runs")
REPORT_PATH = RUNS_DIR / "STELLAI_CORE_EXPANSION_REPORT.md"
EVIDENCE_PATH = RUNS_DIR / "STELLAI_CORE_EXPANSION_EVIDENCE.json"


@dataclass
class Check:
    name: str
    ok: bool
    payload: Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, Any]:
    for attempt in range(6):
        data = None
        final_headers = {"Accept": "application/json"}
        if headers:
            final_headers.update(headers)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            final_headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=final_headers, method=method.upper())
        try:
            with urlopen(req, timeout=120) as response:
                body = response.read().decode("utf-8")
                return response.status, json.loads(body) if body else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"detail": body}
            return exc.code, parsed
        except (URLError, ConnectionResetError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(1)
    raise RuntimeError("unreachable")


def _postgres_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "stellcodex"),
        user=os.environ.get("POSTGRES_USER", "stellcodex"),
        password=os.environ["POSTGRES_PASSWORD"],
    )


def _db_query(sql: str) -> list[list[str]]:
    with _postgres_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            fetched = cur.fetchall()
    rows: list[list[str]] = []
    for row in fetched:
        rows.append([("" if value is None else str(value)) for value in row])
    return rows


def _latest_learning_file() -> dict[str, str]:
    rows = _db_query(
        """
        SELECT file_id, original_filename
        FROM uploaded_files
        WHERE status = 'ready'
        ORDER BY CASE WHEN original_filename ILIKE '%learning%' THEN 0 ELSE 1 END, created_at DESC
        LIMIT 1
        """
    )
    if not rows:
        raise RuntimeError("No ready file found for validation")
    return {"file_id": rows[0][0], "original_filename": rows[0][1]}


def _latest_chat_case(file_id: str) -> dict[str, Any]:
    rows = _db_query(
        f"""
        SELECT c.case_id::text, c.run_type, c.final_status, c.case_type, e.evaluation::text
        FROM ai_case_logs c
        LEFT JOIN ai_eval_results e ON e.case_id = c.case_id
        WHERE c.file_id = '{file_id}' AND c.run_type = 'stellai_chat'
        ORDER BY c.created_at DESC
        LIMIT 1
        """
    )
    if not rows:
        return {}
    evaluation = json.loads(rows[0][4]) if rows[0][4] else {}
    return {
        "case_id": rows[0][0],
        "run_type": rows[0][1],
        "final_status": rows[0][2],
        "case_type": rows[0][3],
        "evaluation": evaluation,
    }


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    direct_tenant_id = int(datetime.now(timezone.utc).timestamp()) % 800000 + 100000

    backend_base = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000/api/v1")
    stellai_base = os.environ["STELLAI_BASE_URL"]
    orchestra_base = os.environ["ORCHESTRA_BASE_URL"]
    target_file = _latest_learning_file()

    checks: list[Check] = []

    backend_health_status, backend_health_payload = _http_json(f"{backend_base}/health")
    checks.append(Check("backend_health", backend_health_status == 200 and backend_health_payload.get("status") == "ok", backend_health_payload))

    stellai_health_status, stellai_health_payload = _http_json(f"{stellai_base}/health")
    checks.append(Check("stellai_health", stellai_health_status == 200 and stellai_health_payload.get("status") == "OK", stellai_health_payload))

    orchestra_health_status, orchestra_health_payload = _http_json(f"{orchestra_base}/health")
    checks.append(Check("orchestra_health", orchestra_health_status == 200 and orchestra_health_payload.get("status") == "OK", orchestra_health_payload))

    direct_before_status, direct_before = _http_json(
        f"{stellai_base}/knowledge/query",
        method="POST",
        payload={"tenant_id": direct_tenant_id, "query": "retrieval layer specification", "max_results": 3},
    )
    checks.append(Check("direct_query_before", direct_before_status == 200, direct_before))

    direct_ingest_status, direct_ingest = _http_json(
        f"{stellai_base}/knowledge/ingest",
        method="POST",
        payload={"tenant_id": direct_tenant_id, "force": True},
    )
    checks.append(Check("direct_ingest", direct_ingest_status == 200 and direct_ingest.get("chunk_count", 0) > 0, direct_ingest))

    direct_after_status, direct_after = _http_json(
        f"{stellai_base}/knowledge/query",
        method="POST",
        payload={"tenant_id": direct_tenant_id, "query": "retrieval layer specification", "max_results": 3},
    )
    checks.append(
        Check(
            "direct_query_after",
            direct_after_status == 200
            and direct_after.get("result_count", 0) > 0
            and bool(direct_after.get("eval", {}).get("improvement_flag")),
            direct_after,
        )
    )

    router_status, router_payload = _http_json(
        f"{stellai_base}/router/route",
        method="POST",
        payload={
            "prompt": "Explain the retrieval layer specification and what changed after ingest.",
            "message_count": 2,
            "knowledge_hits": int(direct_after.get("result_count") or 0),
            "allow_tools": False,
            "file_bound": False,
            "adaptive_boosted": bool(direct_after.get("adaptive_boosted")),
        },
    )
    checks.append(Check("router_decision", router_status == 200 and router_payload.get("router", {}).get("route") == "cheap_model", router_payload))

    tool_status, tool_payload = _http_json(
        f"{stellai_base}/tools/execute",
        method="POST",
        payload={
            "tenant_id": 1,
            "tool_name": "orchestra.sync_file",
            "permission_scope": "orchestra.write",
            "arguments": {"file_id": target_file["file_id"]},
        },
    )
    checks.append(Check("tool_execution", tool_status == 200 and str(tool_payload.get("state") or "").startswith("S"), tool_payload))

    chat_status, chat_payload = _http_json(
        f"{stellai_base}/chat",
        method="POST",
        payload={
            "tenant_id": 1,
            "file_id": target_file["file_id"],
            "message": "Review this learning file and tell me what memory or recovery signals matter.",
            "user_tier": "enterprise",
            "allow_tools": True,
            "requested_tools": [
                {
                    "tool_name": "orchestra.sync_file",
                    "permission_scope": "orchestra.write",
                    "arguments": {"file_id": target_file["file_id"]},
                }
            ],
        },
    )
    checks.append(
        Check(
            "direct_chat",
            chat_status == 200
            and bool(chat_payload.get("session_id"))
            and chat_payload.get("router", {}).get("route") == "premium_model",
            chat_payload,
        )
    )

    session_status, session_payload = _http_json(
        f"{stellai_base}/chat/{chat_payload.get('session_id')}?{urlencode({'tenant_id': 1})}"
    )
    checks.append(Check("chat_persistence", session_status == 200 and len(session_payload.get("messages", [])) >= 2, session_payload))

    auth_status, auth_payload = _http_json(
        f"{backend_base}/auth/login",
        method="POST",
        payload={"email": "ops-admin@stellcodex.com", "password": "SCXAdm1n!2026#Live"},
    )
    token = str(auth_payload.get("access_token") or "")
    auth_headers = {"Authorization": f"Bearer {token}"}
    checks.append(Check("backend_login", auth_status == 200 and bool(token), {"user_id": auth_payload.get("user_id"), "role": auth_payload.get("role")}))

    proxy_ingest_status, proxy_ingest = _http_json(
        f"{backend_base}/stell-ai/knowledge/ingest",
        method="POST",
        payload={"force": True},
        headers=auth_headers,
    )
    checks.append(Check("proxy_ingest", proxy_ingest_status == 200 and proxy_ingest.get("chunk_count", 0) > 0, proxy_ingest))

    proxy_chat_status, proxy_chat = _http_json(
        f"{backend_base}/stell-ai/chat",
        method="POST",
        payload={"message": "Explain the retrieval layer specification after knowledge ingest.", "allow_tools": False},
        headers=auth_headers,
    )
    checks.append(
        Check(
            "proxy_chat",
            proxy_chat_status == 200
            and int(proxy_chat.get("knowledge", {}).get("result_count") or 0) > 0
            and int(proxy_chat.get("tenant_id") or 0) == int(proxy_ingest.get("tenant_id") or -1),
            proxy_chat,
        )
    )

    schema_rows = _db_query(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN (
            'conversation_memory',
            'conversation_messages',
            'knowledge_embeddings',
            'knowledge_memory',
            'stellai_tool_audit_logs',
            'stellai_plugins',
            'ai_case_logs',
            'decision_logs',
            'ai_eval_results',
            'ai_pattern_signals'
          )
        ORDER BY table_name
        """
    )
    schema_tables = [row[0] for row in schema_rows]
    checks.append(Check("schema_tables", len(schema_tables) == 10, schema_tables))

    extension_rows = _db_query("SELECT extname FROM pg_extension ORDER BY extname")
    extensions = [row[0] for row in extension_rows]
    checks.append(Check("vector_extension", "vector" in extensions, extensions))

    chat_case = _latest_chat_case(target_file["file_id"])
    checks.append(
        Check(
            "chat_case_eval",
            bool(chat_case)
            and chat_case.get("run_type") == "stellai_chat"
            and chat_case.get("evaluation", {}).get("accuracy_score") is not None,
            chat_case,
        )
    )

    evidence = {
        "generated_at": _now(),
        "target_file": target_file,
        "direct": {
            "before_query": direct_before,
            "ingest": direct_ingest,
            "after_query": direct_after,
            "router": router_payload,
            "tool": tool_payload,
            "chat": chat_payload,
            "session": session_payload,
        },
        "proxy": {
            "login": {"user_id": auth_payload.get("user_id"), "role": auth_payload.get("role")},
            "ingest": proxy_ingest,
            "chat": proxy_chat,
        },
        "direct_tenant_id": direct_tenant_id,
        "database": {
            "extensions": extensions,
            "tables": schema_tables,
            "chat_case": chat_case,
        },
        "checks": [asdict(check) for check in checks],
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=True, indent=2), encoding="utf-8")

    failures = [check for check in checks if not check.ok]
    report_lines = [
        "# STELL.AI Core Expansion Report",
        "",
        f"Generated at: {_now()}",
        "",
        "## Status",
        "",
        "PASS" if not failures else "FAIL",
        "",
        "## Health",
        "",
        f"- Backend gateway: {'PASS' if checks[0].ok else 'FAIL'}",
        f"- STELL.AI runtime: {'PASS' if checks[1].ok else 'FAIL'}",
        f"- Orchestra runtime: {'PASS' if checks[2].ok else 'FAIL'}",
        f"- pgvector extension: {'PASS' if any(c.name == 'vector_extension' and c.ok for c in checks) else 'FAIL'}",
        "",
        "## Knowledge Engine",
        "",
        f"- Direct query before ingest: result_count={direct_before.get('result_count')} eval={direct_before.get('eval')}",
        f"- Ingest summary: file_count={direct_ingest.get('file_count')} chunk_count={direct_ingest.get('chunk_count')} backend={direct_ingest.get('index_backend')}",
        f"- Direct query after ingest: result_count={direct_after.get('result_count')} adaptive_boosted={direct_after.get('adaptive_boosted')} improvement_flag={direct_after.get('eval', {}).get('improvement_flag')}",
        "",
        "## Conversation Engine",
        "",
        f"- Session id: {chat_payload.get('session_id')}",
        f"- Stored messages: {len(session_payload.get('messages', []))}",
        f"- Router route: {chat_payload.get('router', {}).get('route')}",
        f"- File-bound chat case logged: {chat_case.get('case_id') if chat_case else 'missing'}",
        "",
        "## Tools And Learning",
        "",
        f"- Safe tool execution: orchestra.sync_file -> state={tool_payload.get('state')}",
        f"- Memory signals surfaced in chat: {len(chat_payload.get('learning_context', {}).get('active_signals', []))}",
        f"- Chat eval accuracy: {chat_case.get('evaluation', {}).get('accuracy_score') if chat_case else 'missing'}",
        "",
        "## Multi-Channel Access",
        "",
        f"- Direct REST ingest tenant: {direct_tenant_id}",
        f"- Backend proxy ingest tenant: {proxy_ingest.get('tenant_id')}",
        f"- Backend proxy chat tenant: {proxy_chat.get('tenant_id')}",
        f"- Backend proxy grounded result_count: {proxy_chat.get('knowledge', {}).get('result_count')}",
        "",
        "## Schema",
        "",
        f"- Tables present: {', '.join(schema_tables)}",
        f"- Extensions: {', '.join(extensions)}",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        report_lines.append(f"- {check.name}: {'PASS' if check.ok else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "## Evidence Files",
            "",
            f"- JSON: {EVIDENCE_PATH}",
        ]
    )
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    if failures:
        raise SystemExit("Validation failed; see report for details.")


if __name__ == "__main__":
    main()
