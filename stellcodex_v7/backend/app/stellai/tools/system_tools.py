from __future__ import annotations

import os
import platform
import resource
import shutil
import time
from pathlib import Path
from typing import Any

from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolDefinition, ToolRegistry
from app.stellai.types import RuntimeContext, ToolExecution

_START_TS = time.monotonic()


def build_system_tools(
    *,
    registry: ToolRegistry,
    security_policy: ToolSecurityPolicy | None,
) -> list[ToolDefinition]:
    policy = security_policy or ToolSecurityPolicy()
    return [
        ToolDefinition(
            name="system_info",
            description="Return safe runtime/system metadata without host-sensitive identifiers.",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {"os": {"type": "string"}, "python": {"type": "string"}}},
            permission_scope="stellai.system.read",
            tenant_required=True,
            handler=handle_system_info,
            category="system",
            tags=("read-only",),
        ),
        ToolDefinition(
            name="runtime_status",
            description="Return STELL-AI runtime health and registered tools summary.",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_scope="stellai.system.read",
            tenant_required=True,
            handler=_build_runtime_status_handler(registry=registry, security_policy=policy),
            category="system",
            tags=("read-only", "runtime"),
        ),
        ToolDefinition(
            name="process_status",
            description="Return process-level status for the current STELL-AI worker process.",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_scope="stellai.system.read",
            tenant_required=True,
            handler=handle_process_status,
            category="system",
            tags=("read-only", "process"),
        ),
        ToolDefinition(
            name="disk_usage",
            description="Return disk usage for tenant-safe roots and workspace.",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_scope="stellai.system.read",
            tenant_required=True,
            handler=_build_disk_usage_handler(security_policy=policy),
            category="system",
            tags=("read-only", "filesystem"),
        ),
    ]


def handle_system_info(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
    return ToolExecution(
        tool_name="system_info",
        status="ok",
        output={
            "os": platform.system(),
            "os_release": platform.release(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
    )


def _build_runtime_status_handler(*, registry: ToolRegistry, security_policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        tools = registry.list_tools(include_disabled=True)
        enabled_tools = [item.name for item in tools if item.enabled]
        category_counts: dict[str, int] = {}
        for item in enabled_tools:
            definition = registry.get_tool(item)
            if definition is None:
                continue
            category_counts[definition.category] = category_counts.get(definition.category, 0) + 1
        return ToolExecution(
            tool_name="runtime_status",
            status="ok",
            output={
                "state": "ready",
                "uptime_seconds": round(time.monotonic() - _START_TS, 3),
                "tool_count": len(enabled_tools),
                "categories": category_counts,
                "enabled_tools": enabled_tools,
                "tenant_safe_roots": list(security_policy.allowed_roots(context)),
            },
        )

    return _handler


def handle_process_status(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return ToolExecution(
        tool_name="process_status",
        status="ok",
        output={
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "threads": len(os.listdir(f"/proc/{os.getpid()}/task")) if Path(f"/proc/{os.getpid()}/task").exists() else None,
            "cpu_user_seconds": round(float(usage.ru_utime), 6),
            "cpu_system_seconds": round(float(usage.ru_stime), 6),
            "max_rss_kb": int(usage.ru_maxrss),
        },
    )


def _build_disk_usage_handler(*, security_policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        targets = [Path(root) for root in security_policy.allowed_roots(context)]
        targets.append(Path("/root/workspace"))
        seen: set[Path] = set()
        usage_items: list[dict[str, Any]] = []
        for target in targets:
            resolved = target.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                stats = shutil.disk_usage(resolved)
            except Exception:
                continue
            usage_items.append(
                {
                    "path": str(resolved),
                    "total_bytes": int(stats.total),
                    "used_bytes": int(stats.used),
                    "free_bytes": int(stats.free),
                }
            )
        return ToolExecution(tool_name="disk_usage", status="ok", output={"usage": usage_items})

    return _handler
