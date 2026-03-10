from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class OrchestratorTool(BaseTool):
    name = "orchestrator.status"
    description = "Returns orchestrator session count and recent activity. Read-only."
    permission_scope = "read"
    category = "orchestrator"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        try:
            from app.db.session import SessionLocal
            from app.models.orchestrator import OrchestratorSession
            db = SessionLocal()
            try:
                total = db.query(OrchestratorSession).count()
                tenant_id = str(context.get("tenant_id") or "")
                tenant_total = 0
                if tenant_id:
                    tenant_total = db.query(OrchestratorSession).filter(
                        OrchestratorSession.tenant_id == int(tenant_id)
                    ).count() if tenant_id.isdigit() else 0
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={"total_sessions": total, "tenant_sessions": tenant_total},
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
