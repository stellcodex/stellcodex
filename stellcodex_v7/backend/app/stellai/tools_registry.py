from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from app.stellai.types import RuntimeContext, ToolExecution

ToolHandler = Callable[[RuntimeContext, Optional[Session], Dict[str, Any]], ToolExecution]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permission_scope: str
    tenant_required: bool
    handler: ToolHandler
    category: str
    audit_logging: bool = True
    enabled: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "permission_scope": self.permission_scope,
            "tenant_required": self.tenant_required,
            "category": self.category,
            "audit_logging": self.audit_logging,
            "enabled": self.enabled,
            "tags": list(self.tags),
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._lock = Lock()

    def register_tool(self, definition: ToolDefinition) -> ToolDefinition:
        name = str(definition.name or "").strip()
        if not name:
            raise ValueError("tool name is required")
        with self._lock:
            self._tools[name] = definition
        return definition

    def get_tool(self, name: str) -> ToolDefinition | None:
        key = str(name or "").strip()
        if not key:
            return None
        with self._lock:
            return self._tools.get(key)

    def list_tools(
        self,
        *,
        category: str | None = None,
        include_disabled: bool = False,
    ) -> list[ToolDefinition]:
        with self._lock:
            values = list(self._tools.values())
        out: list[ToolDefinition] = []
        for definition in sorted(values, key=lambda item: item.name):
            if category and definition.category != category:
                continue
            if not include_disabled and not definition.enabled:
                continue
            out.append(definition)
        return out


_DEFAULT_REGISTRY_LOCK = Lock()
_DEFAULT_REGISTRY: ToolRegistry | None = None


def get_default_tool_registry() -> ToolRegistry:
    global _DEFAULT_REGISTRY
    with _DEFAULT_REGISTRY_LOCK:
        if _DEFAULT_REGISTRY is None:
            _DEFAULT_REGISTRY = register_default_tools(ToolRegistry())
        return _DEFAULT_REGISTRY


def register_tool(definition: ToolDefinition, *, registry: ToolRegistry | None = None) -> ToolDefinition:
    target = registry or get_default_tool_registry()
    return target.register_tool(definition)


def get_tool(name: str, *, registry: ToolRegistry | None = None) -> ToolDefinition | None:
    target = registry or get_default_tool_registry()
    return target.get_tool(name)


def list_tools(
    *,
    registry: ToolRegistry | None = None,
    category: str | None = None,
    include_disabled: bool = False,
) -> list[ToolDefinition]:
    target = registry or get_default_tool_registry()
    return target.list_tools(category=category, include_disabled=include_disabled)


def register_default_tools(
    registry: ToolRegistry,
    *,
    retrieval_engine: Any | None = None,
    security_policy: Any | None = None,
) -> ToolRegistry:
    from app.stellai.tools.cad_tools import build_cad_tools
    from app.stellai.tools.core_tools import build_core_tools
    from app.stellai.tools.data_tools import build_data_tools
    from app.stellai.tools.engineering_tools import build_engineering_tools
    from app.stellai.tools.file_tools import build_file_tools
    from app.stellai.tools.research_tools import build_research_tools
    from app.stellai.tools.system_tools import build_system_tools

    for definition in build_core_tools():
        registry.register_tool(definition)
    for definition in build_system_tools(registry=registry, security_policy=security_policy):
        registry.register_tool(definition)
    for definition in build_file_tools(security_policy=security_policy):
        registry.register_tool(definition)
    for definition in build_data_tools(security_policy=security_policy):
        registry.register_tool(definition)
    for definition in build_cad_tools(security_policy=security_policy):
        registry.register_tool(definition)
    for definition in build_engineering_tools():
        registry.register_tool(definition)
    for definition in build_research_tools(retrieval_engine=retrieval_engine):
        registry.register_tool(definition)
    return registry


def reset_default_tool_registry() -> None:
    global _DEFAULT_REGISTRY
    with _DEFAULT_REGISTRY_LOCK:
        _DEFAULT_REGISTRY = None
