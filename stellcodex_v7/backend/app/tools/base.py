"""Base classes for Agent OS tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: Any
    error: str | None = None
    evidence_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "evidence_ref": self.evidence_ref,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    name: str
    description: str
    permission_scope: str = "read"
    requires_approval: bool = False
    category: str = "general"

    @abstractmethod
    def execute(self, params: dict[str, Any], *, context: dict[str, Any]) -> ToolResult:
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permission_scope": self.permission_scope,
            "requires_approval": self.requires_approval,
            "category": self.category,
        }
