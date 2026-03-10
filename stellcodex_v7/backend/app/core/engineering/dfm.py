"""Deterministic DFM report builder for engineering artifacts.

The report assembled here is the canonical structured payload that feeds
persistence, knowledge indexing, and STELL-AI narration.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "stellcodex.v7.dfm_report"
ENGINEERING_DFM_VERSION = "1.1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dedupe_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _categorize_risks(
    risk_analysis: list[dict[str, Any]],
    conflict_flags: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    wall_risks: list[dict[str, Any]] = []
    draft_risks: list[dict[str, Any]] = []
    undercut_risks: list[dict[str, Any]] = []
    shrinkage_warnings: list[dict[str, Any]] = []
    generic_risks: list[dict[str, Any]] = []

    for raw in risk_analysis:
        item = _as_dict(raw)
        if not item:
            continue
        code = str(item.get("code") or item.get("rule_id") or "").strip().lower()
        if "wall" in code or "thin" in code:
            wall_risks.append(item)
        elif "draft" in code:
            draft_risks.append(item)
        elif "undercut" in code:
            undercut_risks.append(item)
        elif "shrinkage" in code:
            shrinkage_warnings.append(item)
        else:
            generic_risks.append(item)

    for flag in conflict_flags:
        token = str(flag or "").strip().lower()
        if not token:
            continue
        if "draft" in token:
            draft_risks.append(
                {
                    "code": token,
                    "severity": "medium",
                    "message": "Draft-related conflict detected by manufacturing decision rules.",
                }
            )
        elif "undercut" in token:
            undercut_risks.append(
                {
                    "code": token,
                    "severity": "medium",
                    "message": "Undercut-related conflict detected by manufacturing decision rules.",
                }
            )
        elif "shrinkage" in token:
            shrinkage_warnings.append(
                {
                    "code": token,
                    "severity": "medium",
                    "message": "Shrinkage-related conflict detected by manufacturing decision rules.",
                }
            )
        elif "wall" in token or "thin" in token:
            wall_risks.append(
                {
                    "code": token,
                    "severity": "medium",
                    "message": "Wall-thickness conflict detected by manufacturing decision rules.",
                }
            )

    risks = wall_risks + draft_risks + undercut_risks + shrinkage_warnings + generic_risks
    return wall_risks, draft_risks, undercut_risks, shrinkage_warnings, risks


def build_engineering_dfm_report(
    *,
    file_id: str,
    mode: str,
    confidence: float,
    rule_version: str,
    rule_explanations: list[str] | None,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    risk_analysis: list[dict[str, Any]] | None,
    recommendations: list[str] | None,
    capability_status: str | None,
    unavailable_reason: str | None,
    deterministic_rules: list[dict[str, Any]] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    geometry_payload = _as_dict(geometry_metrics)
    feature_payload = _as_dict(feature_map)
    manufacturing_payload = _as_dict(manufacturing_decision)
    risk_payload = [_as_dict(item) for item in _as_list(risk_analysis) if _as_dict(item)]
    conflict_flags = _dedupe_strings(_as_list(manufacturing_payload.get("conflict_flags")))
    recommended_changes = _dedupe_strings(
        list(_as_list(manufacturing_payload.get("recommended_changes"))) + list(_as_list(recommendations))
    )
    wall_risks, draft_risks, undercut_risks, shrinkage_warnings, risks = _categorize_risks(risk_payload, conflict_flags)

    report = {
        "schema": SCHEMA_VERSION,
        "version": ENGINEERING_DFM_VERSION,
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "session_id": str(session_id or "") or None,
        "mode": str(mode or "visual_only"),
        "confidence": round(float(confidence or 0.0), 4),
        "rule_version": str(rule_version or ""),
        "rule_explanations": _dedupe_strings(list(rule_explanations or [])),
        "geometry_summary": {
            "bbox": geometry_payload.get("bbox"),
            "volume": geometry_payload.get("volume"),
            "surface_area": geometry_payload.get("surface_area"),
            "part_count": geometry_payload.get("part_count"),
            "triangle_count": geometry_payload.get("triangle_count"),
            "wall_thickness_stats": geometry_payload.get("wall_thickness_stats"),
        },
        "feature_summary": feature_payload,
        "risk_analysis": risk_payload,
        "manufacturing_recommendation": manufacturing_payload,
        "recommended_changes": recommended_changes,
        "conflict_flags": conflict_flags,
        "capability_status": str(capability_status or manufacturing_payload.get("capability_status") or "degraded"),
        "unavailable_reason": str(unavailable_reason or "") or None,
        "wall_risks": wall_risks,
        "draft_risks": draft_risks,
        "undercut_risks": undercut_risks,
        "shrinkage_warnings": shrinkage_warnings,
        "risks": risks,
        "recommendations": recommended_changes if recommended_changes else ["No blocking DFM risks detected by deterministic checks."],
        "deterministic_rules": list(deterministic_rules or []),
    }
    report["report_hash"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return report
