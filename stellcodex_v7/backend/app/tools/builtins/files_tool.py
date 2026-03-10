from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class FilesTool(BaseTool):
    name = "files.status"
    description = "Returns upload status for a given file_id. Read-only."
    permission_scope = "read"
    category = "files"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        file_id = str(params.get("file_id") or "").strip()
        if not file_id:
            return ToolResult(tool=self.name, success=False, output=None, error="file_id required")
        try:
            from app.db.session import SessionLocal
            from app.models.file import UploadFile
            db = SessionLocal()
            try:
                row = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
                if row is None:
                    return ToolResult(tool=self.name, success=False, output=None, error="file not found")
                tenant_id = str(context.get("tenant_id") or "")
                if tenant_id and str(row.tenant_id) != tenant_id:
                    return ToolResult(tool=self.name, success=False, output=None, error="access denied")
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={
                        "file_id": row.file_id,
                        "status": str(row.status),
                        "kind": str((row.meta or {}).get("kind", "unknown")),
                        "tenant_id": str(row.tenant_id),
                    },
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
