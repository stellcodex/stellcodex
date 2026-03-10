from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class ReportTool(BaseTool):
    name = "report.generate"
    description = "Generates a structured Markdown + JSON report for a task. Read-only."
    permission_scope = "read"
    category = "report"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        task_id = str(params.get("task_id") or "").strip()
        if not task_id:
            return ToolResult(tool=self.name, success=False, output=None, error="task_id required")
        try:
            from app.db.session import SessionLocal
            from app.stell_ai.models import AgentTask
            db = SessionLocal()
            try:
                task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
                if task is None:
                    return ToolResult(tool=self.name, success=False, output=None, error="task not found")
                # Tenant isolation
                tenant_id = str(context.get("tenant_id") or "")
                if tenant_id and str(task.tenant_id) != tenant_id:
                    return ToolResult(tool=self.name, success=False, output=None, error="access denied")
                report_md = _render_markdown(task)
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={"task_id": task_id, "markdown": report_md, "status": task.status},
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))


def _render_markdown(task: Any) -> str:
    plan = task.plan_json or {}
    result = task.result_json or {}
    steps = plan.get("steps", [])
    executed = result.get("executed_steps", [])
    lines = [
        f"# Agent Task Report: {task.task_id}",
        f"**Goal:** {task.goal}",
        f"**Status:** {task.status}",
        f"**Risk:** {plan.get('risk_level', 'unknown')}",
        f"**Tenant:** {task.tenant_id}",
        "",
        "## Plan Summary",
        f"Steps planned: {len(steps)}",
        "",
        "## Executed Steps",
    ]
    for step in executed:
        status = "✅" if step.get("success") else "❌"
        lines.append(f"- {status} `{step.get('tool')}` — {step.get('error') or 'ok'}")
    lines += ["", "## Evidence References"]
    for ref in result.get("evidence_refs", []):
        lines.append(f"- {ref}")
    return "\n".join(lines)
