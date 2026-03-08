from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    triggered: bool
    severity: str
    explanation: str
    reference: str
    deterministic_reasoning: str


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _rule_float(rules: dict[str, Any], key: str) -> float:
    if key not in rules:
        raise RuntimeError(f"Missing required rule config: {key}")
    return _as_float(rules.get(key))


def _rule_int(rules: dict[str, Any], key: str) -> int:
    if key not in rules:
        raise RuntimeError(f"Missing required rule config: {key}")
    return _as_int(rules.get(key))


def _rule(
    *,
    rule_id: str,
    triggered: bool,
    severity: str,
    explanation: str,
    deterministic_reasoning: str,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        triggered=bool(triggered),
        severity=str(severity),
        explanation=str(explanation),
        reference=f"STELLCODEX_V7::{rule_id}",
        deterministic_reasoning=str(deterministic_reasoning),
    )


def _bbox_volume_mm3(geometry: dict[str, Any]) -> float:
    bbox = geometry.get("bbox")
    if not isinstance(bbox, dict):
        return 0.0
    x = _as_float(bbox.get("x"))
    y = _as_float(bbox.get("y"))
    z = _as_float(bbox.get("z"))
    if x <= 0 or y <= 0 or z <= 0:
        return 0.0
    return x * y * z


def evaluate_deterministic_rules(meta: dict[str, Any], rules: dict[str, Any]) -> list[dict[str, Any]]:
    geometry = meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else {}
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}
    dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else {}

    quantity = _as_float(meta.get("quantity") or meta.get("requested_quantity") or meta.get("qty"), 1.0)
    tolerance_mm = _as_float(meta.get("tolerance_mm") or geometry.get("tolerance_mm"), 0.25)

    wall_min_mm = _as_float(
        geometry.get("wall_min_mm")
        or (geometry.get("wall_mm") if isinstance(geometry.get("wall_mm"), (int, float)) else None)
        or ((geometry.get("wall") or {}).get("min_mm") if isinstance(geometry.get("wall"), dict) else None),
        0.0,
    )
    wall_max_mm = _as_float(
        geometry.get("wall_max_mm")
        or ((geometry.get("wall") or {}).get("max_mm") if isinstance(geometry.get("wall"), dict) else None),
        wall_min_mm,
    )
    draft_deg_min = _as_float(geometry_report.get("draft_deg_min") or geometry.get("draft_deg_min"), 0.0)
    undercut_count = _as_int(
        geometry_report.get("undercut_count")
        or dfm_findings.get("undercut_count")
        or (1 if bool(geometry_report.get("undercut_detected") or dfm_findings.get("undercut_detected")) else 0),
        0,
    )
    shrinkage_pct = _as_float(
        geometry_report.get("shrinkage_pct")
        or dfm_findings.get("shrinkage_pct")
        or meta.get("material_shrinkage_pct"),
        0.0,
    )
    volume_mm3 = _as_float(
        geometry.get("volume")
        or geometry.get("volume_mm3")
        or _bbox_volume_mm3(geometry),
        0.0,
    )

    quantity_threshold_high = _rule_float(rules, "quantity_threshold_high")
    tolerance_mm_tight = _rule_float(rules, "tolerance_mm_tight")
    wall_mm_min = _rule_float(rules, "wall_mm_min")
    wall_mm_max = _rule_float(rules, "wall_mm_max")
    draft_min_deg = _rule_float(rules, "draft_min_deg")
    undercut_count_warn = _rule_int(rules, "undercut_count_warn")
    shrinkage_warn_pct = _rule_float(rules, "shrinkage_warn_pct")
    shrinkage_block_pct = _rule_float(rules, "shrinkage_block_pct")
    volume_mm3_high = _rule_float(rules, "volume_mm3_high")
    volume_quantity_conflict_limit = _rule_float(rules, "volume_quantity_conflict_limit")

    results: list[RuleResult] = []
    results.append(
        _rule(
            rule_id="quantity_threshold",
            triggered=quantity >= quantity_threshold_high,
            severity="medium",
            explanation=(
                f"Quantity {quantity:g} exceeds threshold {quantity_threshold_high:g}; "
                "high-volume process review required."
            ),
            deterministic_reasoning="Compare requested quantity to rule_configs.quantity_threshold_high.",
        )
    )
    results.append(
        _rule(
            rule_id="tolerance_impact",
            triggered=tolerance_mm > 0 and tolerance_mm <= tolerance_mm_tight,
            severity="medium",
            explanation=(
                f"Tolerance {tolerance_mm:g} mm is tighter than threshold {tolerance_mm_tight:g} mm; "
                "precision process and cost impact expected."
            ),
            deterministic_reasoning="Compare tolerance_mm to rule_configs.tolerance_mm_tight.",
        )
    )

    wall_triggered = (wall_min_mm > 0 and wall_min_mm < wall_mm_min) or (wall_max_mm > wall_mm_max > 0)
    wall_severity = "high" if wall_min_mm > 0 and wall_min_mm < wall_mm_min else "medium"
    results.append(
        _rule(
            rule_id="wall_thickness_rule",
            triggered=wall_triggered,
            severity=wall_severity,
            explanation=(
                f"Wall range [{wall_min_mm:g}, {wall_max_mm:g}] mm violates limits "
                f"[{wall_mm_min:g}, {wall_mm_max:g}] mm."
            ),
            deterministic_reasoning="Validate geometry wall metrics against rule_configs wall bounds.",
        )
    )

    results.append(
        _rule(
            rule_id="draft_requirement",
            triggered=draft_deg_min > 0 and draft_deg_min < draft_min_deg,
            severity="high",
            explanation=f"Draft {draft_deg_min:g} deg is below minimum {draft_min_deg:g} deg.",
            deterministic_reasoning="Compare geometry_report.draft_deg_min to rule_configs.draft_min_deg.",
        )
    )

    results.append(
        _rule(
            rule_id="undercut_detection",
            triggered=undercut_count >= max(1, undercut_count_warn),
            severity="medium" if undercut_count < 3 else "high",
            explanation=f"Detected undercut features count={undercut_count}.",
            deterministic_reasoning="Use deterministic undercut counters from geometry_report/dfm_findings.",
        )
    )

    results.append(
        _rule(
            rule_id="shrinkage_logic",
            triggered=shrinkage_pct >= shrinkage_warn_pct,
            severity="high" if shrinkage_pct >= shrinkage_block_pct else "medium",
            explanation=(
                f"Estimated shrinkage {shrinkage_pct:g}% exceeds warning threshold {shrinkage_warn_pct:g}%."
            ),
            deterministic_reasoning="Compare shrinkage_pct to rule_configs shrinkage thresholds.",
        )
    )

    conflict_mass = volume_mm3 * max(quantity, 1.0)
    volume_conflict = (
        conflict_mass >= volume_quantity_conflict_limit
        or (volume_mm3 >= volume_mm3_high and quantity >= quantity_threshold_high)
    )
    results.append(
        _rule(
            rule_id="volume_quantity_conflict",
            triggered=volume_conflict,
            severity="high",
            explanation=(
                f"Volume/quantity load {conflict_mass:g} (volume={volume_mm3:g}mm3, qty={quantity:g}) "
                f"exceeds limit {volume_quantity_conflict_limit:g}."
            ),
            deterministic_reasoning="Evaluate volume * quantity against conflict limit from rule_configs.",
        )
    )

    return [asdict(item) for item in results]


def summarize_triggered_rules(results: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    risk_flags: list[str] = []
    conflict_flags: list[str] = []
    explanations: list[str] = []
    for item in results:
        if not isinstance(item, dict) or not item.get("triggered"):
            continue
        rule_id = str(item.get("rule_id") or "").strip()
        if not rule_id:
            continue
        severity = str(item.get("severity") or "medium").strip().lower()
        explanation = str(item.get("explanation") or "").strip()
        risk_flags.append(rule_id)
        if severity in {"high", "critical"}:
            conflict_flags.append(rule_id)
        if explanation:
            explanations.append(f"{rule_id}: {explanation}")
    return sorted(set(risk_flags)), sorted(set(conflict_flags)), explanations
