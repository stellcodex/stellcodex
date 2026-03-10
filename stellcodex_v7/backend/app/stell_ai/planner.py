"""Structured planner — produces deterministic execution plan.

Planner does NOT use LLM reasoning. It uses rule-based heuristics to
infer tools and steps from the goal text + retrieval context.
LLM may not override deterministic manufacturing decisions.
"""
from __future__ import annotations

import uuid
from typing import Any

from app.stell_ai.policy import classify_risk, requires_approval
from app.stell_ai.schemas import PlanStep, TaskPlan


# ── Tool inference heuristics ─────────────────────────────────────────────────

_TOOL_HINTS: list[tuple[frozenset[str], str, dict[str, Any]]] = [
    (frozenset({"health", "status", "system", "service"}), "system.health", {}),
    (frozenset({"file", "upload", "uploaded", "files"}), "files.status", {}),
    (frozenset({"job", "queue", "dlq", "pending"}), "jobs.status", {}),
    (frozenset({"orchestrator", "session", "sessions"}), "orchestrator.status", {}),
    (frozenset({"dfm", "manufacturability", "design"}), "dfm.report", {}),
    (frozenset({"knowledge", "search", "find", "lookup", "retrieve", "query"}), "knowledge.search", {}),
    (frozenset({"audit", "events", "log", "history"}), "audit.recent", {}),
    (frozenset({"report", "generate report", "summary"}), "report.generate", {}),
]
_FILE_SCOPED_TOOLS = frozenset({"files.status", "dfm.report"})
_POST_EXECUTION_TOOLS = frozenset({"report.generate"})


def _infer_tools(goal: str, file_ids: list[str]) -> list[tuple[str, dict[str, Any]]]:
    goal_lower = goal.lower()
    words = set(goal_lower.split())
    selected: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for hint_words, tool_name, base_params in _TOOL_HINTS:
        if hint_words & words:
            if tool_name not in seen:
                if tool_name in _POST_EXECUTION_TOOLS:
                    continue
                params = dict(base_params)
                if tool_name in _FILE_SCOPED_TOOLS:
                    if not file_ids:
                        continue
                    params["file_id"] = file_ids[0]
                if tool_name == "knowledge.search":
                    params["query"] = goal
                    params["top_k"] = 5
                selected.append((tool_name, params))
                seen.add(tool_name)
    # Default: always include knowledge search for context
    if "knowledge.search" not in seen:
        selected.append(("knowledge.search", {"query": goal, "top_k": 5}))
    return selected


def build_plan(
    *,
    goal: str,
    file_ids: list[str] | None = None,
    context_refs: list[str] | None = None,
    allowed_tools: frozenset[str] | None = None,
) -> TaskPlan:
    """Build a structured, deterministic execution plan."""
    file_ids = file_ids or []
    inferred = _infer_tools(goal, file_ids)

    # Filter to allowed tools only
    if allowed_tools is not None:
        inferred = [(t, p) for t, p in inferred if t in allowed_tools]

    tool_names = [t for t, _ in inferred]
    risk_level = classify_risk(goal, tool_names)
    approval_required = requires_approval(risk_level)

    steps = [
        PlanStep(
            step_id=f"step_{i + 1:03d}",
            tool=tool_name,
            arguments=params,
            requires_approval=approval_required and tool_name in {"report.generate"},
            rollback_note="Read-only operation; no rollback required."
            if risk_level == "low"
            else "Review output before applying changes.",
        )
        for i, (tool_name, params) in enumerate(inferred)
    ]

    return TaskPlan(
        goal=goal,
        risk_level=risk_level,
        requires_approval=approval_required,
        steps=steps,
        context_refs=context_refs or [],
    )
