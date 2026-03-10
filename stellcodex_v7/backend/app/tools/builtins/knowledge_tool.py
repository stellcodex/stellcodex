from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool, ToolResult


class KnowledgeTool(BaseTool):
    name = "knowledge.search"
    description = "Hybrid knowledge search (vector + BM25). Returns cited records with scores."
    permission_scope = "read"
    category = "knowledge"

    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        query = str(params.get("query") or "").strip()
        top_k = int(params.get("top_k") or 5)
        tenant_id = str(context.get("tenant_id") or "").strip()
        project_id = str(context.get("project_id") or "default").strip()
        if not query:
            return ToolResult(tool=self.name, success=False, output=None, error="query required")
        try:
            from app.db.session import SessionLocal
            from app.knowledge.service import get_knowledge_service
            db = SessionLocal()
            try:
                svc = get_knowledge_service()
                results = svc.search_knowledge(
                    db=db,
                    query=query,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    top_k=max(1, min(top_k, 20)),
                )
                return ToolResult(
                    tool=self.name,
                    success=True,
                    output={
                        "count": len(results),
                        "results": [
                            {
                                "record_id": r.get("record_id"),
                                "title": r.get("title"),
                                "score": r.get("score"),
                                "source_ref": r.get("source_ref"),
                                "text": (r.get("text") or "")[:500],
                            }
                            for r in results
                        ],
                    },
                )
            finally:
                db.close()
        except Exception as exc:
            return ToolResult(tool=self.name, success=False, output=None, error=str(exc))
