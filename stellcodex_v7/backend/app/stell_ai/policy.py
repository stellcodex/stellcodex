"""Permission policies for Agent OS.

Client-supplied permissions are ALWAYS ignored.
Authority is derived server-side from the authenticated principal.
"""
from __future__ import annotations

from typing import Any

# Tools allowed per principal type
_GUEST_TOOLS: frozenset[str] = frozenset({
    "system.health",
    "knowledge.search",
})

_USER_TOOLS: frozenset[str] = frozenset({
    "system.health",
    "files.status",
    "jobs.status",
    "orchestrator.status",
    "dfm.report",
    "knowledge.search",
    "audit.recent",
    "report.generate",
})

_ADMIN_TOOLS: frozenset[str] = frozenset({
    "system.health",
    "files.status",
    "jobs.status",
    "orchestrator.status",
    "dfm.report",
    "knowledge.search",
    "audit.recent",
    "report.generate",
})

_PRIVILEGED_ROLES = frozenset({"admin", "owner", "founder", "service"})
_STANDARD_ROLES = frozenset({"user", "member", "engineer", "operator", "analyst"})

# Risk classification per tool
TOOL_RISK: dict[str, str] = {
    "system.health": "low",
    "files.status": "low",
    "jobs.status": "low",
    "orchestrator.status": "low",
    "dfm.report": "low",
    "knowledge.search": "low",
    "audit.recent": "low",
    "report.generate": "low",
}

# Destructive tools requiring approval
DESTRUCTIVE_TOOLS: frozenset[str] = frozenset()


def resolve_allowed_tools(
    *,
    principal_type: str,
    role: str | None = None,
) -> frozenset[str]:
    """Return server-authoritative allowed tool set. Never trusts client input."""
    if principal_type == "guest":
        return _GUEST_TOOLS
    if principal_type == "user":
        r = str(role or "").strip().lower()
        if r in _PRIVILEGED_ROLES:
            return _ADMIN_TOOLS
        if r in _STANDARD_ROLES:
            return _USER_TOOLS
    return frozenset()


def classify_risk(goal: str, tools: list[str]) -> str:
    """Classify overall task risk level."""
    goal_lower = goal.lower()
    if any(w in goal_lower for w in ("delete", "drop", "destroy", "purge", "wipe")):
        return "critical"
    if any(w in goal_lower for w in ("modify", "update", "write", "change", "patch")):
        return "medium"
    if any(t in DESTRUCTIVE_TOOLS for t in tools):
        return "high"
    return "low"


def requires_approval(risk_level: str) -> bool:
    return risk_level in ("high", "critical")
