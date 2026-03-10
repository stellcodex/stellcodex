from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.core.engineering import build_engineering_dfm_report


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _rule_float(rules: dict[str, Any], key: str) -> float:
    if key not in rules:
        raise RuntimeError(f"Missing required rule config: {key}")
    return _as_float(rules.get(key))


def _validated_decision_json(decision_json: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(decision_json, dict) or not decision_json:
        raise RuntimeError("decision_json is required")

    required = ("mode", "confidence", "rule_version", "rule_explanations")
    missing = [key for key in required if key not in decision_json]
    if missing:
        raise RuntimeError(f"decision_json missing required keys: {missing}")

    mode = str(decision_json.get("mode") or "").strip()
    if not mode:
        raise RuntimeError("decision_json.mode is required")
    if not isinstance(decision_json.get("confidence"), (int, float)):
        raise RuntimeError("decision_json.confidence is required")
    rule_version = str(decision_json.get("rule_version") or "").strip()
    if not rule_version:
        raise RuntimeError("decision_json.rule_version is required")
    if not isinstance(decision_json.get("rule_explanations"), list):
        raise RuntimeError("decision_json.rule_explanations is required")
    return decision_json


def _simple_pdf_bytes(title: str, body: list[str]) -> bytes:
    lines = [f"BT /F1 18 Tf 72 760 Td ({title}) Tj ET"]
    y = 730
    for line in body[:18]:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        lines.append(f"BT /F1 12 Tf 72 {y} Td ({safe}) Tj ET")
        y -= 24
    content = "\n".join(lines).encode("latin-1", errors="ignore")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        f"4 0 obj << /Length {len(content)} >> stream\n".encode("ascii") + content + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    xref_positions: list[int] = []
    out = bytearray(b"%PDF-1.4\n")
    for obj in objects:
        xref_positions.append(len(out))
        out.extend(obj)
    xref_start = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for pos in xref_positions:
        out.extend(f"{pos:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            "trailer << /Size {size} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".format(
                size=len(objects) + 1,
                start=xref_start,
            )
        ).encode("ascii")
    )
    return bytes(out)


def build_dfm_report(
    file_row: Any,
    rules: dict[str, Any],
    decision_json: dict[str, Any],
    deterministic_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    decision_json = _validated_decision_json(decision_json)
    meta = file_row.meta if isinstance(getattr(file_row, "meta", None), dict) else {}
    geometry = meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else {}
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}

    wall_min = _as_float(
        geometry.get("wall_min_mm")
        or (geometry.get("wall_mm") if isinstance(geometry.get("wall_mm"), (int, float)) else None)
        or ((geometry.get("wall") or {}).get("min_mm") if isinstance(geometry.get("wall"), dict) else None),
        0.0,
    )
    wall_max = _as_float(
        geometry.get("wall_max_mm")
        or ((geometry.get("wall") or {}).get("max_mm") if isinstance(geometry.get("wall"), dict) else None),
        wall_min,
    )
    draft_deg_min = _as_float(geometry_report.get("draft_deg_min") or geometry.get("draft_deg_min"), 0.0)
    undercut_count = int(
        _as_float(
            geometry_report.get("undercut_count")
            or (1 if bool(geometry_report.get("undercut_detected")) else 0),
            0,
        )
    )
    shrinkage_pct = _as_float(
        geometry_report.get("shrinkage_pct") or meta.get("material_shrinkage_pct"),
        0.0,
    )

    wall_min_rule = _rule_float(rules, "wall_mm_min")
    wall_max_rule = _rule_float(rules, "wall_mm_max")
    draft_rule = _rule_float(rules, "draft_min_deg")
    shrinkage_warn = _rule_float(rules, "shrinkage_warn_pct")

    wall_risks: list[dict[str, Any]] = []
    draft_risks: list[dict[str, Any]] = []
    undercut_risks: list[dict[str, Any]] = []
    shrinkage_warnings: list[dict[str, Any]] = []
    recommendations: list[str] = []

    if wall_min > 0 and wall_min < wall_min_rule:
        wall_risks.append(
            {
                "code": "wall_too_thin",
                "severity": "high",
                "value_mm": wall_min,
                "threshold_mm": wall_min_rule,
                "message": "Wall thickness below minimum manufacturing threshold.",
            }
        )
        recommendations.append("Increase minimum wall thickness or add reinforcement ribs.")
    if wall_max > wall_max_rule > 0:
        wall_risks.append(
            {
                "code": "wall_too_thick",
                "severity": "medium",
                "value_mm": wall_max,
                "threshold_mm": wall_max_rule,
                "message": "Wall thickness above maximum threshold may cause sink/warp risk.",
            }
        )
        recommendations.append("Core out thick regions to maintain uniform wall thickness.")

    if draft_deg_min > 0 and draft_deg_min < draft_rule:
        draft_risks.append(
            {
                "code": "draft_below_minimum",
                "severity": "high",
                "value_deg": draft_deg_min,
                "threshold_deg": draft_rule,
                "message": "Draft angle below process minimum.",
            }
        )
        recommendations.append("Increase draft angles on pull-direction surfaces.")

    if undercut_count > 0:
        undercut_risks.append(
            {
                "code": "undercut_detected",
                "severity": "medium" if undercut_count < 3 else "high",
                "count": undercut_count,
                "message": "Undercut features require side action or design change.",
            }
        )
        recommendations.append("Remove undercuts or plan side-action tooling.")

    if shrinkage_pct >= shrinkage_warn:
        shrinkage_warnings.append(
            {
                "code": "shrinkage_warning",
                "severity": "medium",
                "value_pct": shrinkage_pct,
                "threshold_pct": shrinkage_warn,
                "message": "Estimated shrinkage exceeds warning threshold.",
            }
        )
        recommendations.append("Compensate nominal geometry for material shrinkage.")

    if not recommendations:
        recommendations.append("No blocking DFM risks detected by deterministic checks.")

    dedup_recommendations: list[str] = []
    seen: set[str] = set()
    for item in recommendations:
        key = str(item).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        dedup_recommendations.append(key)

    engineering_report = meta.get("engineering_dfm_report") if isinstance(meta.get("engineering_dfm_report"), dict) else {}
    engineering_geometry_metrics = meta.get("engineering_geometry_metrics") if isinstance(meta.get("engineering_geometry_metrics"), dict) else {}
    engineering_feature_map = meta.get("engineering_feature_map") if isinstance(meta.get("engineering_feature_map"), dict) else {}
    engineering_analysis = meta.get("engineering_analysis") if isinstance(meta.get("engineering_analysis"), dict) else {}
    manufacturing_decision = engineering_analysis.get("manufacturing_decision") if isinstance(engineering_analysis.get("manufacturing_decision"), dict) else {}
    engineering_risk_analysis = engineering_report.get("risk_analysis") if isinstance(engineering_report.get("risk_analysis"), list) else (
        engineering_analysis.get("dfm_risk") if isinstance(engineering_analysis.get("dfm_risk"), list) else []
    )
    engineering_recommendations = engineering_report.get("recommended_changes") if isinstance(engineering_report.get("recommended_changes"), list) else (
        engineering_analysis.get("recommendations") if isinstance(engineering_analysis.get("recommendations"), list) else []
    )

    report = build_engineering_dfm_report(
        file_id=str(getattr(file_row, "file_id", None) or ""),
        mode=str(decision_json.get("mode") or engineering_analysis.get("mode") or "visual_only"),
        confidence=_as_float(decision_json.get("confidence"), _as_float(engineering_analysis.get("confidence"), 0.05)),
        rule_version=str(decision_json.get("rule_version") or rules.get("rule_version") or "v7.0.0"),
        rule_explanations=[str(item) for item in (decision_json.get("rule_explanations") or [])],
        geometry_metrics=engineering_geometry_metrics,
        feature_map=engineering_feature_map,
        manufacturing_decision=manufacturing_decision,
        risk_analysis=engineering_risk_analysis,
        recommendations=engineering_recommendations,
        capability_status=str(engineering_analysis.get("capability_status") or ""),
        unavailable_reason=str(engineering_analysis.get("unavailable_reason") or "") or None,
        deterministic_rules=deterministic_rules or [],
    )
    report["wall_risks"] = wall_risks + [item for item in (report.get("wall_risks") or []) if isinstance(item, dict)]
    report["draft_risks"] = draft_risks + [item for item in (report.get("draft_risks") or []) if isinstance(item, dict)]
    report["undercut_risks"] = undercut_risks + [item for item in (report.get("undercut_risks") or []) if isinstance(item, dict)]
    report["shrinkage_warnings"] = shrinkage_warnings + [item for item in (report.get("shrinkage_warnings") or []) if isinstance(item, dict)]
    report["recommendations"] = dedup_recommendations + [str(item) for item in (report.get("recommendations") or []) if str(item).strip()]
    report["decision_json"] = sanitize_public_decision_json(decision_json)
    report["legacy_geometry_summary"] = {
        "wall_min_mm": wall_min,
        "wall_max_mm": wall_max,
        "draft_deg_min": draft_deg_min,
        "undercut_count": undercut_count,
        "shrinkage_pct": shrinkage_pct,
    }
    report["risks"] = (
        [item for item in report["wall_risks"] if isinstance(item, dict)]
        + [item for item in report["draft_risks"] if isinstance(item, dict)]
        + [item for item in report["undercut_risks"] if isinstance(item, dict)]
        + [item for item in report["shrinkage_warnings"] if isinstance(item, dict)]
        + [item for item in (report.get("risk_analysis") or []) if isinstance(item, dict)]
    )
    report["report_hash"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report


def sanitize_public_decision_json(decision_json: dict[str, Any]) -> dict[str, Any]:
    payload = dict(decision_json or {})
    forbidden = {"storage_key", "object_key", "bucket", "revision_id"}
    return {key: value for key, value in payload.items() if key not in forbidden}


def build_dfm_pdf(report: dict[str, Any]) -> bytes:
    body = [
        f"file_id: {report.get('file_id')}",
        f"mode: {report.get('mode')}",
        f"confidence: {report.get('confidence')}",
        f"rule_version: {report.get('rule_version')}",
        f"wall_risks: {len(report.get('wall_risks') or [])}",
        f"draft_risks: {len(report.get('draft_risks') or [])}",
        f"undercut_risks: {len(report.get('undercut_risks') or [])}",
        f"shrinkage_warnings: {len(report.get('shrinkage_warnings') or [])}",
        f"report_hash: {report.get('report_hash')}",
    ]
    for rec in (report.get("recommendations") or [])[:8]:
        body.append(f"rec: {str(rec)[:120]}")
    return _simple_pdf_bytes("STELLCODEX DFM Report", body)
