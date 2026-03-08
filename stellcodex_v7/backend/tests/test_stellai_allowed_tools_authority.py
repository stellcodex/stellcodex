from __future__ import annotations

from unittest.mock import patch
import unittest

from app.api.v1.routes import stell_ai
from app.api.v1.routes.stell_ai import RuntimeExecuteIn, ToolRequestIn
from app.security.deps import Principal


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
        for item in request.tool_requests:
            name = str(item.get("name") or "")
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
                "graph_id": "tg_test",
                "nodes": [
                    {
                        "node_id": "n_exec",
                        "kind": "execute_tools",
                        "description": "execute",
                        "depends_on": [],
                        "payload": {"tools": [item.get("name") for item in request.tool_requests]},
                    }
                ],
                "metadata": {"allowed_tools": sorted(request.context.allowed_tools)},
            },
            "retrieval": {"query": request.message, "chunks": []},
            "tool_results": tool_results,
            "memory": {},
            "events": [],
        }
        return _DummyRuntimeResult(payload)


class StellAIAllowedToolsAuthorityTests(unittest.TestCase):
    def _run_route(self, *, body: RuntimeExecuteIn, principal: Principal):
        runtime = _CapturingRuntime()
        with patch.object(stell_ai, "_resolve_runtime_scope", return_value=("1", "default", ())):
            with patch.object(stell_ai, "get_stellai_runtime", return_value=runtime):
                result = stell_ai.execute_stell_ai_runtime(body=body, db=object(), principal=principal)
        return result, runtime

    def test_guest_client_allowed_tools_is_ignored(self) -> None:
        body = RuntimeExecuteIn(
            message="test",
            allowed_tools=["write_file", "runtime.echo"],
            tool_requests=[
                ToolRequestIn(name="write_file", params={}),
                ToolRequestIn(name="runtime.echo", params={}),
            ],
        )
        principal = Principal(typ="guest", owner_sub="guest-1")

        result, runtime = self._run_route(body=body, principal=principal)
        assert runtime.last_request is not None

        effective = runtime.last_request.context.allowed_tools
        self.assertNotIn("write_file", effective)
        self.assertIn("runtime.echo", effective)

        statuses = {item["tool_name"]: item["status"] for item in result.tool_results}
        self.assertEqual(statuses.get("write_file"), "denied")
        self.assertEqual(statuses.get("runtime.echo"), "ok")

    def test_standard_user_cannot_self_grant_write_file(self) -> None:
        body = RuntimeExecuteIn(
            message="test",
            allowed_tools=["write_file"],
            tool_requests=[ToolRequestIn(name="write_file", params={})],
        )
        principal = Principal(typ="user", user_id="u1", role="user", jti="j1")

        result, runtime = self._run_route(body=body, principal=principal)
        assert runtime.last_request is not None

        self.assertNotIn("write_file", runtime.last_request.context.allowed_tools)
        self.assertEqual(result.tool_results[0]["status"], "denied")
        self.assertEqual(result.tool_results[0]["reason"], "tool_not_permitted_for_request")

    def test_admin_role_receives_server_authorized_write_file(self) -> None:
        body = RuntimeExecuteIn(
            message="test",
            allowed_tools=[],
            tool_requests=[ToolRequestIn(name="write_file", params={})],
        )
        principal = Principal(typ="user", user_id="admin-1", role="admin", jti="j2")

        result, runtime = self._run_route(body=body, principal=principal)
        assert runtime.last_request is not None

        self.assertIn("write_file", runtime.last_request.context.allowed_tools)
        self.assertEqual(result.tool_results[0]["status"], "ok")

    def test_unknown_role_defaults_to_least_privilege(self) -> None:
        body = RuntimeExecuteIn(
            message="test",
            allowed_tools=["doc_search", "mesh_info"],
            tool_requests=[
                ToolRequestIn(name="runtime.echo", params={}),
                ToolRequestIn(name="doc_search", params={}),
            ],
        )
        principal = Principal(typ="user", user_id="u2", role="mystery", jti="j3")

        result, runtime = self._run_route(body=body, principal=principal)
        assert runtime.last_request is not None

        self.assertEqual(runtime.last_request.context.allowed_tools, frozenset({"runtime.echo"}))
        statuses = {item["tool_name"]: item["status"] for item in result.tool_results}
        self.assertEqual(statuses.get("runtime.echo"), "ok")
        self.assertEqual(statuses.get("doc_search"), "denied")


if __name__ == "__main__":
    unittest.main()
