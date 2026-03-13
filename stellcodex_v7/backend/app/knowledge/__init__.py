from __future__ import annotations

__all__ = ["KnowledgeService", "get_knowledge_service"]


def __getattr__(name: str):
    if name in {"KnowledgeService", "get_knowledge_service"}:
        from app.knowledge.service import KnowledgeService, get_knowledge_service

        return {
            "KnowledgeService": KnowledgeService,
            "get_knowledge_service": get_knowledge_service,
        }[name]
    raise AttributeError(name)
