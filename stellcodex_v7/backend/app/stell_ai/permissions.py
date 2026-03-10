"""Permission enforcement for Agent OS. Wraps policy module."""
from __future__ import annotations

from app.stell_ai.policy import resolve_allowed_tools, DESTRUCTIVE_TOOLS


def enforce_tool_permission(
    tool_name: str,
    *,
    allowed_tools: frozenset[str],
    approval_granted: bool = False,
) -> tuple[bool, str]:
    """Returns (permitted, reason)."""
    if tool_name not in allowed_tools:
        return False, f"Tool '{tool_name}' not in server-authoritative allowlist"
    if tool_name in DESTRUCTIVE_TOOLS and not approval_granted:
        return False, f"Tool '{tool_name}' requires explicit approval"
    return True, "ok"


def get_principal_allowed_tools(principal: dict) -> frozenset[str]:
    """Derive allowed tools from principal dict (never from client input)."""
    return resolve_allowed_tools(
        principal_type=str(principal.get("type") or "guest"),
        role=principal.get("role"),
    )
