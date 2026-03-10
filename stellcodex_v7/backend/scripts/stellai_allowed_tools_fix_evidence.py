from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_stellcodex")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!!")

from app.api.v1.routes import stell_ai
from app.api.v1.routes.stell_ai import RuntimeExecuteIn, ToolRequestIn
from app.security.deps import Principal
from app.stellai.tools import SafeToolExecutor, ToolCall
from app.stellai.tools.audit import ToolAuditLogger
from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.types import RuntimeContext


class _DummyRuntimeResult:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_dict(self) -> dict:
        return self._payload


class _CapturingRuntime:
    def __init__(self) -> None:
        self.last_request = None

    def run(self, *, request, db=None):
        self.last_request = request
        tool_results = []
        for raw in request.tool_requests:
            name = str(raw.get("name") or "")
            if name in request.context.allowed_tools:
                tool_results.append(
                    {
                        "tool_name": name,
                        "status": "ok",
                        "output": {"status": "ok"},
                        "reason": None,
                    }
                )
            else:
                reason = "tool_not_permitted_for_request"
                tool_results.append(
                    {
                        "tool_name": name,
                        "status": "denied",
                        "output": {"error": {"reason": reason}},
                        "reason": reason,
                    }
                )

        payload = {
            "session_id": request.context.session_id,
            "trace_id": request.context.trace_id,
            "reply": "ok",
            "plan": {
                "graph_id": "tg_fix",
                "nodes": [
                    {
                        "node_id": "n_exec",
                        "kind": "execute_tools",
                        "description": "execute",
                        "depends_on": [],
                        "payload": {"tools": [raw.get("name") for raw in request.tool_requests]},
                    }
                ],
                "metadata": {"allowed_tools": sorted(request.context.allowed_tools)},
            },
            "retrieval": {"query": request.message, "chunks": []},
            "tool_results": tool_results,
            "memory": {},
            "evaluation": {
                "status": "pass",
                "confidence": 0.9,
                "retry_recommended": False,
                "revised": False,
                "issues": [],
                "actions": ["no_changes_required"],
            },
            "events": [],
        }
        return _DummyRuntimeResult(payload)


def main() -> int:
    evidence_dir = Path("/root/workspace/evidence/stellai").resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1) Client-supplied allowed_tools is ignored by server authority policy.
    runtime = _CapturingRuntime()
    body = RuntimeExecuteIn(
        message="security-fix-check",
        allowed_tools=["write_file", "runtime.echo"],
        tool_requests=[
            ToolRequestIn(name="write_file", params={}),
            ToolRequestIn(name="runtime.echo", params={}),
        ],
    )
    principal_guest = Principal(typ="guest", owner_sub="guest-fix")
    with patch.object(stell_ai, "_resolve_runtime_scope", return_value=("1", "default", ())):
        with patch.object(stell_ai, "get_stellai_runtime", return_value=runtime):
            route_result = stell_ai.execute_stell_ai_runtime(body=body, db=object(), principal=principal_guest)

    client_ignored = {
        "client_payload_allowed_tools": body.allowed_tools,
        "effective_allowed_tools": sorted(list(runtime.last_request.context.allowed_tools)) if runtime.last_request else [],
        "tool_results": route_result.tool_results,
        "write_file_granted": bool(runtime.last_request and "write_file" in runtime.last_request.context.allowed_tools),
    }
    (evidence_dir / "tool_client_allowed_tools_ignored.json").write_text(
        json.dumps(client_ignored, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 2) Server authority policy grant/deny behavior + audit proof.
    fs_root = evidence_dir / "tenant_fs_fix"
    policy = ToolSecurityPolicy(base_root=fs_root)
    audit_path = evidence_dir / "tool_permission_fix_audit.jsonl"
    if audit_path.exists():
        audit_path.unlink()
    executor = SafeToolExecutor(
        allowlist=frozenset({"write_file", "runtime.echo"}),
        security_policy=policy,
        audit_logger=ToolAuditLogger(path=audit_path),
    )

    guest_allowed = stell_ai._resolve_server_allowed_tools(
        principal=principal_guest,
        tenant_id="1",
        project_id="default",
        file_ids=(),
    )
    admin_principal = Principal(typ="user", user_id="admin-1", role="admin", jti="j-admin")
    admin_allowed = stell_ai._resolve_server_allowed_tools(
        principal=admin_principal,
        tenant_id="1",
        project_id="default",
        file_ids=(),
    )

    guest_context = RuntimeContext(
        tenant_id="1",
        project_id="default",
        principal_type="guest",
        principal_id="guest-fix",
        session_id="sess_guest_fix",
        trace_id="trace_guest_fix",
        allowed_tools=guest_allowed,
    )
    admin_context = RuntimeContext(
        tenant_id="1",
        project_id="default",
        principal_type="user",
        principal_id="admin-1",
        session_id="sess_admin_fix",
        trace_id="trace_admin_fix",
        allowed_tools=admin_allowed,
    )

    guest_results = executor.execute_calls(
        context=guest_context,
        db=None,
        calls=[
            ToolCall(name="write_file", params={"path": "notes/guest.txt", "content": "guest"}),
            ToolCall(name="runtime.echo", params={"message": "guest"}),
        ],
    )
    admin_results = executor.execute_calls(
        context=admin_context,
        db=None,
        calls=[ToolCall(name="write_file", params={"path": "notes/admin.txt", "content": "admin"})],
    )

    audit_rows: list[dict] = []
    if audit_path.exists():
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                audit_rows.append(json.loads(line))
    status_counts: dict[str, int] = {}
    for row in audit_rows:
        key = str(row.get("status") or "unknown")
        status_counts[key] = status_counts.get(key, 0) + 1

    authority = {
        "guest_allowed_tools": sorted(list(guest_allowed)),
        "admin_allowed_tools_count": len(admin_allowed),
        "guest_results": [item.to_dict() for item in guest_results],
        "admin_results": [item.to_dict() for item in admin_results],
        "audit_log_path": str(audit_path),
        "audit_status_counts": status_counts,
    }
    (evidence_dir / "tool_authority_backed_permissions.json").write_text(
        json.dumps(authority, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "client_allowed_tools_ignored": not client_ignored["write_file_granted"],
        "guest_write_file_denied": guest_results[0].status == "denied",
        "admin_write_file_allowed": admin_results[0].status == "ok",
        "denied_actions_logged": status_counts.get("denied", 0) >= 1,
        "artifacts": [
            str(evidence_dir / "tool_client_allowed_tools_ignored.json"),
            str(evidence_dir / "tool_authority_backed_permissions.json"),
            str(evidence_dir / "tool_permission_fix_audit.jsonl"),
        ],
    }
    (evidence_dir / "tool_permission_fix_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
