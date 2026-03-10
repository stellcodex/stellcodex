"""Executor — runs plan steps sequentially with security enforcement.

Rules:
- Tools must come from registry (server-side).
- Client-supplied permissions are ignored.
- Unknown tool → fail that step.
- Each step produces a structured StepResult.
- Destructive tools require approval_granted in context.
"""
from __future__ import annotations

import logging
from typing import Any

from app.stell_ai.schemas import PlanStep, StepResult, TaskPlan
from app.stell_ai.permissions import enforce_tool_permission
from app.tools.registry import get_tool_registry

log = logging.getLogger(__name__)


def execute_plan(
    plan: TaskPlan,
    *,
    context: dict[str, Any],
    allowed_tools: frozenset[str],
    approval_granted: bool = False,
) -> tuple[list[StepResult], list[StepResult]]:
    """Execute all steps. Returns (executed_steps, failed_steps)."""
    registry = get_tool_registry()
    executed: list[StepResult] = []
    failed: list[StepResult] = []

    for step in plan.steps:
        result = _execute_step(
            step,
            registry=registry,
            context=context,
            allowed_tools=allowed_tools,
            approval_granted=approval_granted,
        )
        if result.success:
            executed.append(result)
        else:
            failed.append(result)
            log.warning(
                "executor.step_failed step_id=%s tool=%s error=%s",
                step.step_id, step.tool, result.error,
            )

    return executed, failed


def _execute_step(
    step: PlanStep,
    *,
    registry: Any,
    context: dict[str, Any],
    allowed_tools: frozenset[str],
    approval_granted: bool,
) -> StepResult:
    # Permission enforcement — server-side authority only
    permitted, reason = enforce_tool_permission(
        step.tool,
        allowed_tools=allowed_tools,
        approval_granted=approval_granted,
    )
    if not permitted:
        log.warning("executor.blocked tool=%s reason=%s", step.tool, reason)
        return StepResult(
            step_id=step.step_id,
            tool=step.tool,
            success=False,
            output=None,
            error=reason,
        )

    tool_result = registry.execute(
        step.tool,
        step.arguments,
        context=context,
        allowed_tools=allowed_tools,
    )

    evidence_ref = (
        f"tool:{step.tool}:{step.step_id}"
        if tool_result.success
        else None
    )

    return StepResult(
        step_id=step.step_id,
        tool=step.tool,
        success=tool_result.success,
        output=tool_result.output,
        error=tool_result.error,
        evidence_ref=evidence_ref,
    )
