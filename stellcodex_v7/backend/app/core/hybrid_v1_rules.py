from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.hybrid_v1_geometry import CRITICAL_GEOMETRY_FIELDS, build_geometry_report_for_step


def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "unknown", "none", "null", "n/a", "na"}
    return False


def _to_float(value: Any) -> float | None:
    if _is_unknown(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in {"1", "true", "yes", "y"}:
            return True
        if token in {"0", "false", "no", "n"}:
            return False
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in values:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


REQUIRED_RUNTIME_RULE_KEYS: tuple[str, ...] = (
    "draft_min_deg",
    "wall_mm_min",
    "wall_mm_max",
)


def _require_runtime_rules(config: dict[str, Any] | None) -> dict[str, Any]:
    cfg = dict(config or {})
    missing = [key for key in REQUIRED_RUNTIME_RULE_KEYS if key not in cfg]
    if missing:
        raise RuntimeError(f"Missing runtime rule config keys: {missing}")
    return cfg


def evaluate_hybrid_v1_rules(
    geometry_report: dict[str, Any],
    config: dict[str, Any] | None = None,
    runner_mode: str | None = None,
) -> dict[str, Any]:
    cfg = _require_runtime_rules(config)
    geometry = geometry_report.get("geometry", {})
    if not isinstance(geometry, dict):
        geometry = {}

    findings: list[dict[str, Any]] = []
    risk_flags: list[str] = []

    critical_unknowns: set[str] = set()
    report_unknowns = geometry_report.get("critical_unknowns", [])
    if isinstance(report_unknowns, list):
        critical_unknowns.update(str(item) for item in report_unknowns)
    for field in CRITICAL_GEOMETRY_FIELDS:
        if field in geometry and _is_unknown(geometry.get(field)):
            critical_unknowns.add(field)

    if critical_unknowns:
        risk_flags.append("unknown_critical_geometry")
        findings.append(
            {
                "code": "unknown_critical_geometry",
                "severity": "blocking",
                "message": "Critical geometry is unknown; manual review is required.",
                "fields": sorted(critical_unknowns),
            }
        )

    draft_min_actual = _to_float(geometry.get("draft_deg_min"))
    draft_min_required = float(cfg["draft_min_deg"])
    if draft_min_actual is not None and draft_min_actual < draft_min_required:
        risk_flags.append("draft_below_min")
        findings.append(
            {
                "code": "draft_below_min",
                "severity": "blocking",
                "message": f"Minimum draft angle {draft_min_actual:.3f} is below required {draft_min_required:.3f}.",
            }
        )

    wall_min_actual = _to_float(geometry.get("wall_mm_min"))
    wall_max_actual = _to_float(geometry.get("wall_mm_max"))
    wall_min_required = float(cfg["wall_mm_min"])
    wall_max_allowed = float(cfg["wall_mm_max"])

    if wall_min_actual is not None and wall_min_actual < wall_min_required:
        risk_flags.append("wall_below_min")
        findings.append(
            {
                "code": "wall_below_min",
                "severity": "blocking",
                "message": f"Minimum wall {wall_min_actual:.3f} mm is below required {wall_min_required:.3f} mm.",
            }
        )
    if wall_max_actual is not None and wall_max_actual > wall_max_allowed:
        risk_flags.append("wall_above_max")
        findings.append(
            {
                "code": "wall_above_max",
                "severity": "blocking",
                "message": f"Maximum wall {wall_max_actual:.3f} mm is above allowed {wall_max_allowed:.3f} mm.",
            }
        )

    undercut = _to_bool(geometry.get("has_undercut"))
    if undercut is True:
        risk_flags.append("undercut_detected")
        findings.append(
            {
                "code": "undercut_detected",
                "severity": "blocking",
                "message": "Undercut detected; tooling approval required.",
            }
        )

    complexity_risk_raw = geometry.get("complexity_risk")
    complexity_risk = _to_bool(complexity_risk_raw)
    complexity_risk_label = str(complexity_risk_raw).strip().lower()
    complexity_label = str(geometry.get("complexity", "")).strip().lower()
    if complexity_risk is True or complexity_risk_label == "high" or complexity_label in {"high", "complex"}:
        risk_flags.append("complexity_risk")
        findings.append(
            {
                "code": "complexity_risk",
                "severity": "blocking",
                "message": "Part complexity requires manual approval.",
            }
        )

    mode_raw = runner_mode
    if mode_raw is None:
        process_meta = geometry_report.get("process", {})
        if isinstance(process_meta, dict):
            mode_raw = process_meta.get("runner_mode")
    if mode_raw is None:
        mode_raw = cfg.get("runner_mode_default") or "cold"
    mode = str(mode_raw).strip().lower()
    if mode == "hot":
        risk_flags.append("hot_runner_requested")
        findings.append(
            {
                "code": "hot_runner_requested",
                "severity": "blocking",
                "message": "Hot runner requested; approval is required by policy.",
            }
        )

    status_gate = "NEEDS_APPROVAL" if any(item.get("severity") == "blocking" for item in findings) else "PASS"

    return {
        "schema": "hybrid_v1.dfm_findings",
        "status_gate": status_gate,
        "risk_flags": _unique(risk_flags),
        "findings": findings,
        "runner_mode": mode,
        "config": cfg,
    }


def run_hybrid_v1_step_pipeline(
    step_path: str | Path,
    config: dict[str, Any] | None = None,
    runner_mode: str | None = None,
    provided_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    geometry_report = build_geometry_report_for_step(step_path, provided_inputs=provided_inputs)
    dfm_findings = evaluate_hybrid_v1_rules(geometry_report, config=config, runner_mode=runner_mode)
    return {"geometry_report": geometry_report, "dfm_findings": dfm_findings}
