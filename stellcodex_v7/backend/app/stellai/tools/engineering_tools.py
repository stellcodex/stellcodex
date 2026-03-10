"""STELL-AI tool wrappers for deterministic engineering analysis.

Keep tool outputs aligned with the engineering runtime contract so planner,
executor, and reply composition stay predictable.
"""

from __future__ import annotations

from typing import Any

from app.core.identity.stell_identity import ANALYSIS_UNAVAILABLE_TEXT
from app.stellai.engineering.analysis import (
    analysis_limits,
    analyze_upload,
    load_upload_for_tenant,
    resolve_file_id,
)
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution


def build_engineering_tools() -> list[ToolDefinition]:
    definitions: list[tuple[str, str]] = [
        ("cad_load", "Validate file security and detect the deterministic engineering capability path."),
        ("mesh_analyze", "Run guarded mesh or STEP analysis under deterministic capability rules."),
        ("volume_compute", "Return deterministic volume where the active capability path supports it."),
        ("surface_area_compute", "Return deterministic surface area where the active capability path supports it."),
        ("feature_extract", "Return deterministic feature flags and capability status."),
        ("dfm_precheck", "Run deterministic precheck rules without overstating unsupported formats."),
    ]
    return [
        ToolDefinition(
            name=name,
            description=description,
            input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]},
            output_schema={"type": "object"},
            permission_scope="stellai.engineering.read",
            tenant_required=True,
            handler=_build_handler(name),
            category="engineering",
            tags=("engineering", "deterministic"),
        )
        for name, description in definitions
    ]


def _build_handler(tool_name: str):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        try:
            file_id = resolve_file_id(str(params.get("file_id") or ""), context.file_ids)
            row = load_upload_for_tenant(db, file_id=file_id, tenant_id=context.tenant_id)
            result = analyze_upload(row)
        except Exception as exc:
            reason = getattr(exc, "code", "analysis_unavailable")
            return ToolExecution(
                tool_name=tool_name,
                status="failed",
                reason=str(reason),
                output={
                    "message": ANALYSIS_UNAVAILABLE_TEXT,
                    "limits": analysis_limits(),
                },
            )

        payload = dict(result)
        if tool_name == "cad_load":
            payload = {
                "file_id": result.get("file_id"),
                "mode": result.get("mode"),
                "confidence": result.get("confidence"),
                "capability_status": result.get("capability_status"),
                "unavailable_reason": result.get("unavailable_reason"),
                "limits": analysis_limits(),
            }
        elif tool_name == "volume_compute":
            payload = {
                "file_id": result.get("file_id"),
                "mode": result.get("mode"),
                "confidence": result.get("confidence"),
                "capability_status": result.get("capability_status"),
                "volume": result.get("volume"),
                "unavailable_reason": result.get("unavailable_reason"),
            }
        elif tool_name == "surface_area_compute":
            payload = {
                "file_id": result.get("file_id"),
                "mode": result.get("mode"),
                "confidence": result.get("confidence"),
                "capability_status": result.get("capability_status"),
                "surface_area": result.get("surface_area"),
                "unavailable_reason": result.get("unavailable_reason"),
            }
        elif tool_name == "feature_extract":
            payload = {
                "file_id": result.get("file_id"),
                "mode": result.get("mode"),
                "confidence": result.get("confidence"),
                "capability_status": result.get("capability_status"),
                "geometry_metrics": result.get("geometry_metrics"),
                "feature_map": result.get("feature_map"),
                "feature_flags": result.get("feature_flags"),
                "bounding_box": result.get("bounding_box"),
                "unavailable_reason": result.get("unavailable_reason"),
            }
        elif tool_name == "dfm_precheck":
            payload = {
                "file_id": result.get("file_id"),
                "mode": result.get("mode"),
                "confidence": result.get("confidence"),
                "capability_status": result.get("capability_status"),
                "recommended_process": result.get("recommended_process"),
                "manufacturing_decision": result.get("manufacturing_decision"),
                "manufacturing_plan": result.get("manufacturing_plan"),
                "cost_estimate": result.get("cost_estimate"),
                "dfm_report": result.get("dfm_report"),
                "engineering_report": result.get("engineering_report"),
                "dfm_risk": result.get("dfm_risk"),
                "recommendations": result.get("recommendations"),
                "rule_version": result.get("rule_version"),
                "rule_explanations": result.get("rule_explanations"),
                "unavailable_reason": result.get("unavailable_reason"),
            }

        status = "ok" if not payload.get("unavailable_reason") else "failed"
        reason = None if status == "ok" else "analysis_unavailable"
        return ToolExecution(tool_name=tool_name, status=status, reason=reason, output=payload)

    return _handler
