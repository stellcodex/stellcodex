"""Tool registry — server-side allowlist enforcement.

Client-supplied permissions are IGNORED. Authority is resolved server-side
from the authenticated principal's role.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from threading import Lock
from typing import Any

from app.tools.base import BaseTool, ToolResult

log = logging.getLogger(__name__)

_DESTRUCTIVE_SCOPES = frozenset({"write", "admin", "delete"})


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._lock = Lock()

    def register(self, tool: BaseTool) -> None:
        with self._lock:
            self._tools[tool.name] = tool
        log.debug("tool_registry.registered name=%s scope=%s", tool.name, tool.permission_scope)

    def get(self, name: str) -> BaseTool | None:
        with self._lock:
            return self._tools.get(str(name or "").strip())

    def list_tools(self) -> list[dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self._tools.values()]

    def execute(
        self,
        name: str,
        params: dict[str, Any],
        *,
        context: dict[str, Any],
        allowed_tools: frozenset[str] | set[str] | None = None,
    ) -> ToolResult:
        """Execute a tool with allowlist enforcement.

        If allowed_tools is provided, the tool name must be in it.
        Destructive tools require explicit approval in context.
        """
        tool = self.get(name)
        if tool is None:
            log.warning("tool_registry.unknown_tool name=%s", name)
            return ToolResult(
                tool=name,
                success=False,
                output=None,
                error=f"Unknown tool: {name}",
            )

        # Allowlist enforcement — client permissions ignored
        if allowed_tools is not None and name not in allowed_tools:
            log.warning("tool_registry.blocked name=%s", name)
            return ToolResult(
                tool=name,
                success=False,
                output=None,
                error=f"Tool not permitted for this principal: {name}",
            )

        # Destructive approval gate
        if tool.requires_approval:
            approved = bool(context.get("approval_granted"))
            if not approved:
                return ToolResult(
                    tool=name,
                    success=False,
                    output=None,
                    error=f"Tool {name} requires explicit approval",
                )

        try:
            result = tool.execute(params, context=context)
            log.debug("tool_registry.executed name=%s success=%s", name, result.success)
            return result
        except Exception as exc:
            log.error("tool_registry.execution_error name=%s: %s", name, exc)
            return ToolResult(
                tool=name,
                success=False,
                output=None,
                error=str(exc),
            )


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    from app.tools.builtins import register_all_builtins
    registry = ToolRegistry()
    register_all_builtins(registry)
    return registry
