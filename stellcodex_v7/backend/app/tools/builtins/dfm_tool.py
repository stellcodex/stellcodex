from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class DfmTool(BaseTool):
    name = "dfm.report"
    description = "Returns DFM report for a given file_id from knowledge records. Read-only."
    permission_scope = "read"
    category = "dfm"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        file_id = str(params.get("file_id") or "").strip()
        tenant_id = str(context.get("tenant_id") or "").strip()
        if not file_id:
            return ToolResult(tool=self.name, success=False, output=None, error="file_id required")
        try:
            from app.db.session import SessionLocal
            from app.models.knowledge import KnowledgeRecord
            db = SessionLocal()
            try:
                q = db.query(KnowledgeRecord).filter(
                    KnowledgeRecord.file_id == file_id,
                    KnowledgeRecord.source_type == "dfm_report",
                )
                if tenant_id:
                    q = q.filter(KnowledgeRecord.tenant_id == int(tenant_id))
                row = q.first()
                if row is None:
                    return ToolResult(tool=self.name, success=True, output={"found": False, "file_id": file_id})
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={
                        "found": True,
                        "record_id": row.record_id,
                        "title": row.title,
                        "summary": row.summary,
                        "source_ref": row.source_ref,
                        "embedding_status": row.embedding_status,
                    },
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
