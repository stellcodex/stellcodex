"""Reporter — generates JSON + Markdown task reports."""
from __future__ import annotations

from typing import Any

from app.stell_ai.schemas import StepResult, TaskPlan, TaskResult


def generate_report(
    *,
    task_id: str,
    goal: str,
    status: str,
    plan: TaskPlan,
    executed_steps: list[StepResult],
    failed_steps: list[StepResult],
    evidence_refs: list[str] | None = None,
) -> TaskResult:
    evidence_refs = evidence_refs or [
        s.evidence_ref for s in executed_steps if s.evidence_ref
    ]

    report_json = _build_json(
        task_id=task_id,
        goal=goal,
        status=status,
        plan=plan,
        executed_steps=executed_steps,
        failed_steps=failed_steps,
        evidence_refs=evidence_refs,
    )

    report_md = _build_markdown(
        task_id=task_id,
        goal=goal,
        status=status,
        plan=plan,
        executed_steps=executed_steps,
        failed_steps=failed_steps,
        evidence_refs=evidence_refs,
    )

    return TaskResult(
        task_id=task_id,
        goal=goal,
        status=status,
        risk_level=plan.risk_level,
        plan=plan,
        executed_steps=executed_steps,
        failed_steps=failed_steps,
        evidence_refs=evidence_refs,
        report_markdown=report_md,
        report_json=report_json,
    )


def _build_json(
    *,
    task_id: str,
    goal: str,
    status: str,
    plan: TaskPlan,
    executed_steps: list[StepResult],
    failed_steps: list[StepResult],
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "goal": goal,
        "status": status,
        "risk_level": plan.risk_level,
        "requires_approval": plan.requires_approval,
        "plan_summary": {
            "step_count": len(plan.steps),
            "tools": [s.tool for s in plan.steps],
        },
        "executed_steps": [s.model_dump() for s in executed_steps],
        "failed_steps": [s.model_dump() for s in failed_steps],
        "evidence_refs": evidence_refs,
        "success_rate": (
            len(executed_steps) / max(len(plan.steps), 1)
        ),
    }


def _build_markdown(
    *,
    task_id: str,
    goal: str,
    status: str,
    plan: TaskPlan,
    executed_steps: list[StepResult],
    failed_steps: list[StepResult],
    evidence_refs: list[str],
) -> str:
    lines = [
        f"# STELLCODEX Agent Task Report",
        f"",
        f"**Task ID:** `{task_id}`",
        f"**Goal:** {goal}",
        f"**Status:** {status}",
        f"**Risk Level:** {plan.risk_level}",
        f"**Requires Approval:** {plan.requires_approval}",
        f"",
        f"## Plan Summary",
        f"Steps planned: {len(plan.steps)}",
        f"Tools: {', '.join(s.tool for s in plan.steps)}",
        f"",
        f"## Executed Steps ({len(executed_steps)})",
    ]
    for s in executed_steps:
        lines.append(f"- ✅ `{s.tool}` (step `{s.step_id}`)")
        if s.evidence_ref:
            lines.append(f"  - Evidence: `{s.evidence_ref}`")

    if failed_steps:
        lines += [f"", f"## Failed Steps ({len(failed_steps)})"]
        for s in failed_steps:
            lines.append(f"- ❌ `{s.tool}` (step `{s.step_id}`) — {s.error}")

    if evidence_refs:
        lines += [f"", f"## Evidence References"]
        for ref in evidence_refs:
            lines.append(f"- `{ref}`")

    success_rate = len(executed_steps) / max(len(plan.steps), 1) * 100
    lines += [
        f"",
        f"## Summary",
        f"Success rate: {success_rate:.0f}% ({len(executed_steps)}/{len(plan.steps)} steps)",
    ]

    return "\n".join(lines)
