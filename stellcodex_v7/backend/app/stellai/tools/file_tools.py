from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution

MAX_READ_BYTES = 262_144
MAX_WRITE_BYTES = 262_144
MAX_LIST_ENTRIES = 500
MAX_SEARCH_FILES = 200
MAX_SEARCH_MATCHES = 200


def build_file_tools(*, security_policy: ToolSecurityPolicy | None) -> list[ToolDefinition]:
    policy = security_policy or ToolSecurityPolicy()
    return [
        ToolDefinition(
            name="read_file",
            description="Read a UTF-8 text file within tenant-safe roots.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer"},
                },
                "required": ["path"],
            },
            output_schema={"type": "object"},
            permission_scope="stellai.files.read",
            tenant_required=True,
            handler=_build_read_file_handler(policy),
            category="file",
            tags=("tenant", "filesystem"),
        ),
        ToolDefinition(
            name="write_file",
            description="Write text content to a file within tenant-safe roots.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"]},
                },
                "required": ["path", "content"],
            },
            output_schema={"type": "object"},
            permission_scope="stellai.files.write",
            tenant_required=True,
            handler=_build_write_file_handler(policy),
            category="file",
            tags=("tenant", "filesystem"),
        ),
        ToolDefinition(
            name="list_directory",
            description="List files and directories under a tenant-safe root.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "recursive": {"type": "boolean"},
                    "max_entries": {"type": "integer"},
                },
            },
            output_schema={"type": "object"},
            permission_scope="stellai.files.read",
            tenant_required=True,
            handler=_build_list_directory_handler(policy),
            category="file",
            tags=("tenant", "filesystem"),
        ),
        ToolDefinition(
            name="search_files",
            description="Search text in files under tenant-safe roots.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {"type": "string"},
                    "regex": {"type": "boolean"},
                    "glob": {"type": "string"},
                    "max_matches": {"type": "integer"},
                },
                "required": ["pattern"],
            },
            output_schema={"type": "object"},
            permission_scope="stellai.files.read",
            tenant_required=True,
            handler=_build_search_files_handler(policy),
            category="file",
            tags=("tenant", "filesystem"),
        ),
    ]


def _build_read_file_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        raw_path = str(params.get("path") or "")
        max_bytes = _bounded_int(params.get("max_bytes"), default=MAX_READ_BYTES, minimum=1, maximum=MAX_READ_BYTES)
        validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=False)
        if not validated.allowed or validated.path is None:
            return _denied("read_file", validated.reason or "path_denied", raw_path)
        path = validated.path
        try:
            with path.open("rb") as handle:
                payload = handle.read(max_bytes + 1)
        except Exception as exc:
            return ToolExecution(
                tool_name="read_file",
                status="failed",
                reason="read_error",
                output={"error": {"reason": "read_error", "detail": str(exc), "path": raw_path}},
            )
        truncated = len(payload) > max_bytes
        text = payload[:max_bytes].decode("utf-8", errors="ignore")
        return ToolExecution(
            tool_name="read_file",
            status="ok",
            output={
                "path": str(path),
                "tenant_root": str(validated.tenant_root),
                "size_bytes": len(payload[:max_bytes]),
                "truncated": truncated,
                "content": text,
            },
        )

    return _handler


def _build_write_file_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        raw_path = str(params.get("path") or "")
        content = str(params.get("content") or "")
        mode = str(params.get("mode") or "overwrite").strip().lower()
        if mode not in {"overwrite", "append"}:
            return ToolExecution(
                tool_name="write_file",
                status="denied",
                reason="invalid_mode",
                output={"error": {"reason": "invalid_mode", "mode": mode}},
            )
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_WRITE_BYTES:
            return ToolExecution(
                tool_name="write_file",
                status="denied",
                reason="content_too_large",
                output={"error": {"reason": "content_too_large", "max_bytes": MAX_WRITE_BYTES}},
            )
        validated = policy.validate_path(
            context=context,
            raw_path=raw_path,
            for_write=True,
            must_exist=False,
            expect_directory=False,
        )
        if not validated.allowed or validated.path is None:
            return _denied("write_file", validated.reason or "path_denied", raw_path)
        path = validated.path
        try:
            write_mode = "a" if mode == "append" else "w"
            with path.open(write_mode, encoding="utf-8") as handle:
                handle.write(content)
        except Exception as exc:
            return ToolExecution(
                tool_name="write_file",
                status="failed",
                reason="write_error",
                output={"error": {"reason": "write_error", "detail": str(exc), "path": raw_path}},
            )
        return ToolExecution(
            tool_name="write_file",
            status="ok",
            output={
                "path": str(path),
                "tenant_root": str(validated.tenant_root),
                "bytes_written": len(encoded),
                "mode": mode,
            },
        )

    return _handler


def _build_list_directory_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        raw_path = str(params.get("path") or ".")
        recursive = bool(params.get("recursive", False))
        max_entries = _bounded_int(params.get("max_entries"), default=120, minimum=1, maximum=MAX_LIST_ENTRIES)
        validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=True)
        if not validated.allowed or validated.path is None:
            return _denied("list_directory", validated.reason or "path_denied", raw_path)
        root = validated.path
        entries: list[dict[str, Any]] = []
        iterator = root.rglob("*") if recursive else root.iterdir()
        for item in iterator:
            if len(entries) >= max_entries:
                break
            try:
                stat = item.stat()
            except Exception:
                continue
            entries.append(
                {
                    "path": str(item),
                    "relative_path": str(item.relative_to(validated.tenant_root)),
                    "is_dir": item.is_dir(),
                    "size_bytes": int(stat.st_size),
                }
            )
        return ToolExecution(
            tool_name="list_directory",
            status="ok",
            output={
                "path": str(root),
                "tenant_root": str(validated.tenant_root),
                "recursive": recursive,
                "entry_count": len(entries),
                "entries": entries,
            },
        )

    return _handler


def _build_search_files_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        raw_path = str(params.get("path") or ".")
        pattern = str(params.get("pattern") or "")
        if not pattern:
            return ToolExecution(
                tool_name="search_files",
                status="denied",
                reason="missing_pattern",
                output={"error": {"reason": "missing_pattern"}},
            )
        glob = str(params.get("glob") or "**/*")
        regex_mode = bool(params.get("regex", False))
        max_matches = _bounded_int(params.get("max_matches"), default=40, minimum=1, maximum=MAX_SEARCH_MATCHES)
        validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=True)
        if not validated.allowed or validated.path is None:
            return _denied("search_files", validated.reason or "path_denied", raw_path)

        try:
            matcher = re.compile(pattern) if regex_mode else None
        except re.error as exc:
            return ToolExecution(
                tool_name="search_files",
                status="denied",
                reason="invalid_regex",
                output={"error": {"reason": "invalid_regex", "detail": str(exc)}},
            )

        matches: list[dict[str, Any]] = []
        scanned = 0
        for path in validated.path.glob(glob):
            if scanned >= MAX_SEARCH_FILES or len(matches) >= max_matches:
                break
            if not path.is_file():
                continue
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                found = bool(matcher.search(line)) if matcher else (pattern in line)
                if not found:
                    continue
                matches.append(
                    {
                        "path": str(path),
                        "relative_path": str(path.relative_to(validated.tenant_root)),
                        "line": idx,
                        "snippet": line[:400],
                    }
                )
                if len(matches) >= max_matches:
                    break

        return ToolExecution(
            tool_name="search_files",
            status="ok",
            output={
                "path": str(validated.path),
                "pattern": pattern,
                "regex": regex_mode,
                "scanned_files": scanned,
                "match_count": len(matches),
                "matches": matches,
            },
        )

    return _handler


def _denied(tool_name: str, reason: str, raw_path: str) -> ToolExecution:
    return ToolExecution(
        tool_name=tool_name,
        status="denied",
        reason=reason,
        output={"error": {"reason": reason, "path": raw_path}},
    )


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(parsed, maximum))
