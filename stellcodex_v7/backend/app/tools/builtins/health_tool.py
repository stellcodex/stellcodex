from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class HealthTool(BaseTool):
    name = "system.health"
    description = "Returns current system health status for all services."
    permission_scope = "read"
    category = "system"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        import subprocess
        results: dict[str, Any] = {}
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:18000/api/v1/health", timeout=2)
            results["backend"] = "ok"
        except Exception:
            results["backend"] = "unreachable"
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:7010/health", timeout=2)
            results["orchestrator"] = "ok"
        except Exception:
            results["orchestrator"] = "unreachable"
        results["redis"] = self._check_redis()
        return ToolResult(tool=self.name, success=True, output=results)

    def _check_redis(self) -> str:
        try:
            from redis import Redis
            r = Redis.from_url("redis://localhost:16379/0", socket_connect_timeout=1)
            r.ping()
            return "ok"
        except Exception:
            return "unreachable"
