from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class AuditTool(BaseTool):
    name = "audit.recent"
    description = "Returns recent audit events for the current tenant. Read-only."
    permission_scope = "read"
    category = "audit"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        limit = int(params.get("limit") or 10)
        tenant_id = str(context.get("tenant_id") or "").strip()
        try:
            from app.db.session import SessionLocal
            from app.models.audit import AuditEvent
            db = SessionLocal()
            try:
                q = db.query(AuditEvent).order_by(AuditEvent.created_at.desc())
                rows = q.limit(max(1, min(limit, 50))).all()
                events = []
                for row in rows:
                    # Never expose storage_key or revision_id
                    detail = row.detail if isinstance(row.detail, dict) else {}
                    safe_detail = {k: v for k, v in detail.items() if k not in {"storage_key", "revision_id", "secret"}}
                    events.append({
                        "id": str(row.id),
                        "action": str(row.action),
                        "actor": str(row.actor or ""),
                        "resource": str(row.resource or ""),
                        "created_at": str(row.created_at),
                    })
                return ToolResult(tool=self.name, success=True, output={"count": len(events), "events": events})
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
