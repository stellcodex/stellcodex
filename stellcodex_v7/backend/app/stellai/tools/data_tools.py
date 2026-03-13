from __future__ import annotations

import json
from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback path
    np = None

try:
    import pandas as pd
except Exception:  # pragma: no cover - fallback path
    pd = None

from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution


def build_data_tools(*, security_policy: ToolSecurityPolicy | None) -> list[ToolDefinition]:
    policy = security_policy or ToolSecurityPolicy()
    return [
        ToolDefinition(
            name="csv_reader",
            description="Read CSV data from a tenant-safe file path.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}, "nrows": {"type": "integer"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.data.read",
            tenant_required=True,
            handler=_build_csv_reader_handler(policy),
            category="data",
            tags=("analytics", "csv"),
        ),
        ToolDefinition(
            name="data_summary",
            description="Generate summary statistics for CSV data in tenant-safe storage.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.data.read",
            tenant_required=True,
            handler=_build_data_summary_handler(policy),
            category="data",
            tags=("analytics", "summary"),
        ),
        ToolDefinition(
            name="data_filter",
            description="Filter CSV rows using declarative conditions.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "filters": {"type": "array"},
                    "limit": {"type": "integer"},
                },
                "required": ["path", "filters"],
            },
            output_schema={"type": "object"},
            permission_scope="stellai.data.read",
            tenant_required=True,
            handler=_build_data_filter_handler(policy),
            category="data",
            tags=("analytics", "filter"),
        ),
        ToolDefinition(
            name="json_transform",
            description="Transform JSON input using safe built-in operations.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.data.read",
            tenant_required=True,
            handler=_build_json_transform_handler(policy),
            category="data",
            tags=("analytics", "json"),
        ),
    ]


def _build_csv_reader_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        dependency_issue = _assert_data_dependencies("csv_reader")
        if dependency_issue is not None:
            return dependency_issue
        loaded = _load_csv(policy=policy, context=context, params=params, tool_name="csv_reader")
        if isinstance(loaded, ToolExecution):
            return loaded
        df = loaded
        preview = df.head(_bounded_int(params.get("preview_rows"), default=10, minimum=1, maximum=50))
        return ToolExecution(
            tool_name="csv_reader",
            status="ok",
            output={
                "row_count": int(df.shape[0]),
                "column_count": int(df.shape[1]),
                "columns": [str(col) for col in df.columns],
                "dtypes": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
                "preview": preview.to_dict(orient="records"),
            },
        )

    return _handler


def _build_data_summary_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        dependency_issue = _assert_data_dependencies("data_summary")
        if dependency_issue is not None:
            return dependency_issue
        loaded = _load_csv(policy=policy, context=context, params=params, tool_name="data_summary")
        if isinstance(loaded, ToolExecution):
            return loaded
        df = loaded
        summary = df.describe(include="all").fillna("")
        numeric_columns = list(df.select_dtypes(include=["number"]).columns)
        correlation: dict[str, Any] = {}
        if numeric_columns and np is not None and len(numeric_columns) > 1:
            corr = df[numeric_columns].corr().replace({np.nan: 0.0})
            correlation = corr.round(6).to_dict()
        return ToolExecution(
            tool_name="data_summary",
            status="ok",
            output={
                "row_count": int(df.shape[0]),
                "column_count": int(df.shape[1]),
                "numeric_columns": [str(item) for item in numeric_columns],
                "summary": summary.to_dict(),
                "correlation": correlation,
            },
        )

    return _handler


def _build_data_filter_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        dependency_issue = _assert_data_dependencies("data_filter")
        if dependency_issue is not None:
            return dependency_issue
        loaded = _load_csv(policy=policy, context=context, params=params, tool_name="data_filter")
        if isinstance(loaded, ToolExecution):
            return loaded
        df = loaded
        raw_filters = params.get("filters")
        if not isinstance(raw_filters, list) or not raw_filters:
            return ToolExecution(
                tool_name="data_filter",
                status="denied",
                reason="missing_filters",
                output={"error": {"reason": "missing_filters"}},
            )

        filtered = df
        for item in raw_filters:
            if not isinstance(item, dict):
                continue
            column = str(item.get("column") or "")
            operator = str(item.get("op") or "eq").lower()
            value = item.get("value")
            if column not in filtered.columns:
                return ToolExecution(
                    tool_name="data_filter",
                    status="denied",
                    reason="unknown_column",
                    output={"error": {"reason": "unknown_column", "column": column}},
                )
            series = filtered[column]
            if operator == "eq":
                filtered = filtered[series == value]
            elif operator == "ne":
                filtered = filtered[series != value]
            elif operator == "gt":
                filtered = filtered[series > value]
            elif operator == "gte":
                filtered = filtered[series >= value]
            elif operator == "lt":
                filtered = filtered[series < value]
            elif operator == "lte":
                filtered = filtered[series <= value]
            elif operator == "contains":
                filtered = filtered[series.astype(str).str.contains(str(value), na=False)]
            elif operator == "in":
                candidates = value if isinstance(value, list) else [value]
                filtered = filtered[series.isin(candidates)]
            else:
                return ToolExecution(
                    tool_name="data_filter",
                    status="denied",
                    reason="invalid_operator",
                    output={"error": {"reason": "invalid_operator", "operator": operator}},
                )

        limit = _bounded_int(params.get("limit"), default=25, minimum=1, maximum=200)
        preview = filtered.head(limit)
        return ToolExecution(
            tool_name="data_filter",
            status="ok",
            output={
                "row_count": int(filtered.shape[0]),
                "column_count": int(filtered.shape[1]),
                "preview": preview.to_dict(orient="records"),
            },
        )

    return _handler


def _build_json_transform_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        payload = params.get("data")
        if payload is None:
            raw_path = str(params.get("path") or "")
            if not raw_path:
                return ToolExecution(
                    tool_name="json_transform",
                    status="denied",
                    reason="missing_data",
                    output={"error": {"reason": "missing_data"}},
                )
            validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=False)
            if not validated.allowed or validated.path is None:
                return ToolExecution(
                    tool_name="json_transform",
                    status="denied",
                    reason=validated.reason,
                    output={"error": {"reason": validated.reason}},
                )
            try:
                payload = json.loads(validated.path.read_text(encoding="utf-8"))
            except Exception:
                return ToolExecution(
                    tool_name="json_transform",
                    status="failed",
                    reason="json_parse_error",
                    output={"error": {"reason": "json_parse_error"}},
                )

        operation = str(params.get("operation") or "identity").strip().lower()
        if operation == "identity":
            transformed = payload
        elif operation == "select_keys":
            keys = params.get("keys") if isinstance(params.get("keys"), list) else []
            if not isinstance(payload, dict):
                return ToolExecution(
                    tool_name="json_transform",
                    status="denied",
                    reason="select_keys_requires_object",
                    output={"error": {"reason": "select_keys_requires_object"}},
                )
            transformed = {str(key): payload.get(key) for key in keys}
        elif operation == "rename_keys":
            mapping = params.get("mapping") if isinstance(params.get("mapping"), dict) else {}
            if not isinstance(payload, dict):
                return ToolExecution(
                    tool_name="json_transform",
                    status="denied",
                    reason="rename_keys_requires_object",
                    output={"error": {"reason": "rename_keys_requires_object"}},
                )
            transformed = {str(mapping.get(key, key)): value for key, value in payload.items()}
        elif operation == "flatten":
            if not isinstance(payload, dict):
                return ToolExecution(
                    tool_name="json_transform",
                    status="denied",
                    reason="flatten_requires_object",
                    output={"error": {"reason": "flatten_requires_object"}},
                )
            transformed = _flatten_dict(payload)
        else:
            return ToolExecution(
                tool_name="json_transform",
                status="denied",
                reason="unsupported_operation",
                output={"error": {"reason": "unsupported_operation", "operation": operation}},
            )

        return ToolExecution(
            tool_name="json_transform",
            status="ok",
            output={"operation": operation, "data": transformed},
        )

    return _handler


def _load_csv(*, policy: ToolSecurityPolicy, context: RuntimeContext, params: dict[str, Any], tool_name: str):
    raw_path = str(params.get("path") or "")
    if not raw_path:
        return ToolExecution(
            tool_name=tool_name,
            status="denied",
            reason="missing_path",
            output={"error": {"reason": "missing_path"}},
        )
    validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=False)
    if not validated.allowed or validated.path is None:
        return ToolExecution(
            tool_name=tool_name,
            status="denied",
            reason=validated.reason,
            output={"error": {"reason": validated.reason}},
        )
    try:
        nrows = _bounded_int(params.get("nrows"), default=2000, minimum=1, maximum=10_000)
        df = pd.read_csv(validated.path, nrows=nrows)
        return df
    except Exception:
        return ToolExecution(
            tool_name=tool_name,
            status="failed",
            reason="csv_read_error",
            output={"error": {"reason": "csv_read_error"}},
        )


def _assert_data_dependencies(tool_name: str) -> ToolExecution | None:
    missing: list[str] = []
    if pd is None:
        missing.append("pandas")
    if np is None:
        missing.append("numpy")
    if not missing:
        return None
    return ToolExecution(
        tool_name=tool_name,
        status="failed",
        reason="dependency_missing",
        output={"error": {"reason": "dependency_missing", "missing": missing}},
    )


def _flatten_dict(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        segment = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(_flatten_dict(value, prefix=segment))
        else:
            out[segment] = value
    return out


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(parsed, maximum))
