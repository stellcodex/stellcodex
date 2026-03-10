from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class JobsTool(BaseTool):
    name = "jobs.status"
    description = "Returns job queue counts by status. Read-only."
    permission_scope = "read"
    category = "jobs"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        try:
            from app.db.session import SessionLocal
            from app.models.phase2 import DlqRecord
            from app.models.knowledge import KnowledgeIndexJob
            db = SessionLocal()
            try:
                dlq_count = db.query(DlqRecord).count()
                ke_pending = db.query(KnowledgeIndexJob).filter(KnowledgeIndexJob.status == "pending").count()
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={"dlq_records": dlq_count, "knowledge_jobs_pending": ke_pending},
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
