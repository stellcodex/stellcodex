from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.rule_engine import evaluate_deterministic_rules, summarize_triggered_rules
from app.models.file import UploadFile
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.services.mfg_classifier import classify_manufacturing_process


RULE_VERSION_FALLBACK = "v7.0.0"
REQUIRED_RULE_CONFIG_KEYS: tuple[str, ...] = (
    "rule_version",
    "draft_min_deg",
    "wall_mm_min",
    "wall_mm_max",
    "block_on_unknown_critical",
    "force_approval_on_visual_only",
    "allow_hot_runner",
    "legacy_backfill_confidence",
    "manufacturing_unknown_confidence_floor",
    "manufacturing_fallback_method",
    "quantity_threshold_high",
    "tolerance_mm_tight",
    "undercut_count_warn",
    "shrinkage_warn_pct",
    "shrinkage_block_pct",
    "volume_mm3_high",
    "volume_quantity_conflict_limit",
)

RULE_CONFIG_DESCRIPTIONS: dict[str, str] = {
    "rule_version": "Canonical rule config version for deterministic decisions",
    "draft_min_deg": "Minimum draft angle in degrees",
    "wall_mm_min": "Minimum wall thickness (mm)",
    "wall_mm_max": "Maximum wall thickness (mm)",
    "block_on_unknown_critical": "Block auto-approval if critical geometry fields are unknown",
    "force_approval_on_visual_only": "Visual-only mode requires manual approval",
    "allow_hot_runner": "Hot runner disabled by default",
    "legacy_backfill_confidence": "Fallback confidence for legacy/backfilled sessions",
    "manufacturing_unknown_confidence_floor": "Minimum confidence floor when manufacturing method is unknown",
    "manufacturing_fallback_method": "Fallback manufacturing method when geometry is insufficient",
    "quantity_threshold_high": "Quantity threshold triggering high-volume deterministic review",
    "tolerance_mm_tight": "Tolerance threshold requiring precision process review",
    "undercut_count_warn": "Undercut count threshold requiring tooling review",
    "shrinkage_warn_pct": "Shrinkage percentage warning threshold",
    "shrinkage_block_pct": "Shrinkage percentage hard-block threshold",
    "volume_mm3_high": "High volume threshold for process conflict checks",
    "volume_quantity_conflict_limit": "Volume*quantity conflict limit",
}

RULE_CONFIG_BOOTSTRAP_PATH = Path(__file__).with_name("rule_config_bootstrap.json")

CANONICAL_STATES: tuple[str, ...] = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7")
STATE_LABELS: dict[str, str] = {
    "S0": "uploaded",
    "S1": "converted",
    "S2": "assembly_ready",
    "S3": "analyzing",
    "S4": "dfm_ready",
    "S5": "awaiting_approval",
    "S6": "approved",
    "S7": "share_ready",
}
ALLOWED_MODES: tuple[str, ...] = ("brep", "mesh_approx", "visual_only")
REQUIRED_DECISION_KEYS: tuple[str, ...] = (
    "rule_version",
    "mode",
    "confidence",
    "manufacturing_method",
    "rule_explanations",
    "conflict_flags",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_rule_bootstrap_values() -> dict[str, Any]:
    payload = json.loads(RULE_CONFIG_BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid rule bootstrap format: {RULE_CONFIG_BOOTSTRAP_PATH}")
    missing = [key for key in REQUIRED_RULE_CONFIG_KEYS if key not in payload]
    if missing:
        raise RuntimeError(
            f"Rule bootstrap missing keys {missing}: {RULE_CONFIG_BOOTSTRAP_PATH}"
        )
    return payload


def seed_default_rule_configs(db: Session) -> None:
    bootstrap_values = _load_rule_bootstrap_values()
    changed = False
    for key in REQUIRED_RULE_CONFIG_KEYS:
        row = db.query(RuleConfig).filter(RuleConfig.key == key).first()
        next_payload = {
            "value": bootstrap_values[key],
            "version": str(bootstrap_values.get("rule_version") or RULE_VERSION_FALLBACK),
            "scope": "global",
        }
        if row is None:
            row = RuleConfig(
                key=key,
                value_json=next_payload,
                enabled=True,
                description=RULE_CONFIG_DESCRIPTIONS.get(key),
            )
            db.add(row)
            changed = True
            continue

        existing = row.value_json if isinstance(row.value_json, dict) else {}
        merged = {
            "value": existing.get("value", bootstrap_values[key]),
            "version": str(existing.get("version") or bootstrap_values.get("rule_version") or RULE_VERSION_FALLBACK),
            "scope": str(existing.get("scope") or "global"),
        }
        if existing != merged:
            row.value_json = merged
            db.add(row)
            changed = True
    if changed:
        db.commit()


def load_rule_config_map(db: Session) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for row in db.query(RuleConfig).filter(RuleConfig.enabled.is_(True)).all():
        if not isinstance(row.value_json, dict):
            continue
        if "value" in row.value_json:
            config[row.key] = row.value_json["value"]
    missing = [key for key in REQUIRED_RULE_CONFIG_KEYS if key not in config]
    if missing:
        raise RuntimeError(f"Missing required enabled rule_configs: {missing}")
    return config


def _rule_as_float(rules: dict[str, Any], key: str) -> float:
    value = rules.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        raise RuntimeError(f"Invalid float rule_configs value for key='{key}': {value!r}")


def _rule_as_bool(rules: dict[str, Any], key: str) -> bool:
    value = rules.get(key)
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
    raise RuntimeError(f"Invalid boolean rule_configs value for key='{key}': {value!r}")


def _as_list_of_str(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _normalize_mode(value: Any) -> str:
    token = str(value or "").strip().lower()
    if token in ALLOWED_MODES:
        return token
    return "visual_only"


def _mode_from_file(file_row: UploadFile) -> str:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    raw_mode = meta.get("mode")
    if isinstance(raw_mode, str):
        token = raw_mode.strip().lower()
        if token in ALLOWED_MODES:
            return token

    lower_name = str(file_row.original_filename or "").strip().lower()
    if lower_name.endswith((".step", ".stp", ".iges", ".igs")):
        return "brep"
    if lower_name.endswith((".stl", ".obj")):
        return "mesh_approx"
    if lower_name.endswith((".glb", ".gltf")):
        return "visual_only"
    return "visual_only"


def _status_to_base_state(status: str) -> str:
    token = (status or "").strip().lower()
    if token in {"pending", ""}:
        return "S0"
    if token in {"queued"}:
        return "S1"
    if token in {"running", "processing"}:
        return "S3"
    if token in {"failed", "ready", "succeeded"}:
        return "S4"
    return "S2"


def _state_label(state: str) -> str:
    return STATE_LABELS.get(state, STATE_LABELS["S0"])


def _is_valid_transition_path(previous_state: str, target_state: str, raw_path: Any) -> bool:
    if not isinstance(raw_path, list) or len(raw_path) < 2:
        return False
    path = [str(item) for item in raw_path]
    if path[0] != previous_state or path[-1] != target_state:
        return False
    for left, right in zip(path, path[1:]):
        if left not in CANONICAL_STATES or right not in CANONICAL_STATES:
            return False
        if CANONICAL_STATES.index(right) - CANONICAL_STATES.index(left) != 1:
            return False
    return True


def _rule_version(rules: dict[str, Any]) -> str:
    token = str(rules.get("rule_version") or "").strip()
    return token or RULE_VERSION_FALLBACK


def _clamp_confidence(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = fallback
    if parsed < 0:
        return 0.0
    if parsed > 1:
        return 1.0
    return round(parsed, 4)


def _manufacturing_signal(meta: dict[str, Any], rules: dict[str, Any]) -> tuple[str, float, list[str], list[str]]:
    fallback_method = str(rules.get("manufacturing_fallback_method") or "manual_review").strip() or "manual_review"
    confidence_floor = _clamp_confidence(rules.get("manufacturing_unknown_confidence_floor"), 0.05)
    geometry_meta = meta.get("geometry_meta_json")
    if not isinstance(geometry_meta, dict) or not geometry_meta:
        return (
            fallback_method,
            confidence_floor,
            ["legacy_backfill: manufacturing method fallback applied due missing geometry meta."],
            ["manufacturing_geometry_missing"],
        )

    result = classify_manufacturing_process(geometry_meta)
    method = str(result.process or fallback_method)
    confidence = _clamp_confidence(result.confidence, confidence_floor)
    explanations = [str(item) for item in (result.reasons or []) if str(item).strip()]
    if not explanations:
        explanations = ["manufacturing method selected by deterministic rule engine."]
    conflict_flags: list[str] = []
    if method == "unknown":
        conflict_flags.append("manufacturing_unknown")
        confidence = max(confidence, confidence_floor)
    return method, confidence, explanations, conflict_flags


def _apply_manual_approval_override(meta: dict[str, Any], current_state: str) -> tuple[str, str, bool, list[str], list[str]]:
    override = str(meta.get("approval_override") or "").strip().lower()
    if override == "approved":
        return (
            "S7",
            "PASS",
            False,
            ["manual approval granted; transitioned through S5->S6->S7."],
            [],
        )
    if override == "rejected":
        return (
            "S4",
            "NEEDS_APPROVAL",
            True,
            ["manual approval rejected; returned to S4 for policy-compliant rework."],
            ["approval_rejected"],
        )
    return current_state, "PENDING", False, [], []


def build_decision_json(file_row: UploadFile, rules: dict[str, Any]) -> dict[str, Any]:
    draft_min_deg = _rule_as_float(rules, "draft_min_deg")
    wall_mm_min = _rule_as_float(rules, "wall_mm_min")
    wall_mm_max = _rule_as_float(rules, "wall_mm_max")
    block_on_unknown_critical = _rule_as_bool(rules, "block_on_unknown_critical")
    force_approval_on_visual_only = _rule_as_bool(rules, "force_approval_on_visual_only")
    allow_hot_runner = _rule_as_bool(rules, "allow_hot_runner")
    legacy_confidence = _clamp_confidence(rules.get("legacy_backfill_confidence"), 0.05)
    version = _rule_version(rules)

    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    kind = str(meta.get("kind") or "3d").strip().lower()
    mode = _mode_from_file(file_row)
    base_state = _status_to_base_state(file_row.status)
    state = base_state
    status_gate = "PENDING"
    risk_flags: list[str] = []
    conflict_flags: list[str] = []
    rule_explanations: list[str] = []

    manufacturing_method, confidence, manufacturing_reasons, manufacturing_flags = _manufacturing_signal(meta, rules)
    rule_explanations.extend(manufacturing_reasons)
    conflict_flags.extend(manufacturing_flags)

    if str(file_row.status or "").strip().lower() == "failed":
        status_gate = "REJECTED"
        risk_flags.append("file_processing_failed")
        conflict_flags.append("processing_failed")
        rule_explanations.append("file processing failed before deterministic DFM approval.")
        state = "S4"
        confidence = legacy_confidence

    if kind == "3d" and base_state == "S4" and status_gate != "REJECTED":
        dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else {}
        geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}
        critical_unknowns = _as_list_of_str(geometry_report.get("critical_unknowns"))

        raw_gate = str(dfm_findings.get("status_gate") or "PASS").strip().upper()
        status_gate = raw_gate if raw_gate in {"PASS", "NEEDS_APPROVAL", "REJECTED"} else "PASS"
        risk_flags.extend(_as_list_of_str(dfm_findings.get("risk_flags")))
        raw_findings = dfm_findings.get("findings")
        if isinstance(raw_findings, list):
            for item in raw_findings:
                if isinstance(item, dict):
                    code = str(item.get("code") or "").strip()
                    if code:
                        conflict_flags.append(code)

        if block_on_unknown_critical and critical_unknowns:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("unknown_critical_geometry")
            conflict_flags.append("unknown_critical_geometry")
            rule_explanations.append("critical geometry unknown; policy blocks auto-approval.")

        if mode == "visual_only" and force_approval_on_visual_only:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("visual_only_mode")
            conflict_flags.append("visual_only_mode")
            rule_explanations.append("visual_only mode requires manual approval by policy.")

        runner_mode = str(dfm_findings.get("runner_mode") or "").strip().lower()
        if runner_mode == "hot" and not allow_hot_runner:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("hot_runner_requested")
            conflict_flags.append("hot_runner_requested")
            rule_explanations.append("hot runner blocked by policy; manual approval required.")

        if status_gate == "PASS":
            state = "S6"
            rule_explanations.append("deterministic DFM checks passed.")
        elif status_gate == "NEEDS_APPROVAL":
            state = "S5"
            rule_explanations.append("deterministic DFM checks require approval.")
        elif status_gate == "REJECTED":
            state = "S4"
            conflict_flags.append("dfm_rejected")
            rule_explanations.append("deterministic DFM checks rejected by policy.")
    elif kind != "3d" and base_state == "S4" and status_gate != "REJECTED":
        status_gate = "PASS"
        state = "S6"
        rule_explanations.append("non-3d artifact auto-approved by deterministic policy.")

    override_state, override_gate, override_approval_required, override_reasons, override_flags = _apply_manual_approval_override(
        meta, state
    )
    if override_state != state or override_reasons:
        state = override_state
        status_gate = override_gate
        rule_explanations.extend(override_reasons)
        conflict_flags.extend(override_flags)
        risk_flags.extend(override_flags)
    approval_required = override_approval_required or state == "S5"

    if state not in CANONICAL_STATES:
        state = "S0"
    if not rule_explanations:
        rule_explanations = ["legacy_backfill: default deterministic decision applied."]

    if status_gate not in {"PENDING", "PASS", "NEEDS_APPROVAL", "REJECTED"}:
        status_gate = "PENDING"

    decision = "manual_review"
    if state in {"S6", "S7"} and not approval_required:
        decision = "approve"
    elif status_gate == "REJECTED":
        decision = "reject"

    dedup_risk = sorted({item for item in risk_flags if item})
    dedup_conflicts = sorted({item for item in conflict_flags if item})
    dedup_explanations = []
    seen: set[str] = set()
    for item in [str(x) for x in rule_explanations if str(x).strip()]:
        if item in seen:
            continue
        seen.add(item)
        dedup_explanations.append(item)

    deterministic_rules = evaluate_deterministic_rules(meta, rules)
    rr_risks, rr_conflicts, rr_explanations = summarize_triggered_rules(deterministic_rules)
    dedup_risk = sorted(set(dedup_risk + rr_risks))
    dedup_conflicts = sorted(set(dedup_conflicts + rr_conflicts))
    dedup_explanations = dedup_explanations + [item for item in rr_explanations if item and item not in dedup_explanations]

    return {
        "schema": "stellcodex.v7.decision_json",
        "version": "1.1",
        "state": state,
        "state_code": state,
        "state_label": _state_label(state),
        "status_gate": status_gate,
        "decision": decision,
        "approval_required": approval_required,
        "risk_flags": dedup_risk,
        "conflict_flags": dedup_conflicts,
        "rule_version": version,
        "mode": mode,
        "confidence": _clamp_confidence(confidence, legacy_confidence),
        "manufacturing_method": manufacturing_method,
        "rule_explanations": dedup_explanations,
        "deterministic_rules": deterministic_rules,
        "thresholds": {
            "draft_min_deg": draft_min_deg,
            "wall_mm_min": wall_mm_min,
            "wall_mm_max": wall_mm_max,
            "block_on_unknown_critical": block_on_unknown_critical,
            "force_approval_on_visual_only": force_approval_on_visual_only,
            "allow_hot_runner": allow_hot_runner,
            "quantity_threshold_high": _rule_as_float(rules, "quantity_threshold_high"),
            "tolerance_mm_tight": _rule_as_float(rules, "tolerance_mm_tight"),
            "undercut_count_warn": int(_rule_as_float(rules, "undercut_count_warn")),
            "shrinkage_warn_pct": _rule_as_float(rules, "shrinkage_warn_pct"),
            "shrinkage_block_pct": _rule_as_float(rules, "shrinkage_block_pct"),
            "volume_mm3_high": _rule_as_float(rules, "volume_mm3_high"),
            "volume_quantity_conflict_limit": _rule_as_float(rules, "volume_quantity_conflict_limit"),
        },
        "file_id": file_row.file_id,
        "updated_at": _now_iso(),
    }


def normalize_decision_json(
    file_row: UploadFile,
    rules: dict[str, Any],
    decision_json: Any,
) -> dict[str, Any]:
    canonical = build_decision_json(file_row, rules)
    if not isinstance(decision_json, dict):
        return canonical

    merged = {**canonical, **decision_json}
    merged["state"] = str(merged.get("state") or merged.get("state_code") or canonical["state"])
    if merged["state"] not in CANONICAL_STATES:
        merged["state"] = canonical["state"]
    merged["state_code"] = merged["state"]
    merged["state_label"] = str(merged.get("state_label") or _state_label(merged["state"]))
    merged["status_gate"] = str(merged.get("status_gate") or canonical["status_gate"]).upper()
    if merged["status_gate"] not in {"PENDING", "PASS", "NEEDS_APPROVAL", "REJECTED"}:
        merged["status_gate"] = canonical["status_gate"]
    merged["approval_required"] = bool(merged.get("approval_required"))
    merged["risk_flags"] = _as_list_of_str(merged.get("risk_flags"))
    merged["conflict_flags"] = _as_list_of_str(merged.get("conflict_flags"))
    merged["rule_explanations"] = _as_list_of_str(merged.get("rule_explanations")) or canonical["rule_explanations"]
    merged["mode"] = _normalize_mode(merged.get("mode"))
    merged["rule_version"] = str(merged.get("rule_version") or canonical["rule_version"])
    merged["confidence"] = _clamp_confidence(merged.get("confidence"), canonical["confidence"])
    merged["manufacturing_method"] = str(
        merged.get("manufacturing_method") or canonical["manufacturing_method"]
    )
    merged["updated_at"] = _now_iso()

    missing = [key for key in REQUIRED_DECISION_KEYS if key not in merged or merged.get(key) in (None, "", [])]
    if missing:
        return canonical
    return merged


def upsert_orchestrator_session(db: Session, file_row: UploadFile, decision_json: dict[str, Any]) -> OrchestratorSession:
    row = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()
    previous_state = row.state if row is not None and isinstance(row.state, str) else None
    if row is None:
        row = OrchestratorSession(file_id=file_row.file_id)
        db.add(row)

    state = str(decision_json.get("state") or decision_json.get("state_code") or "S0")
    if state not in CANONICAL_STATES:
        state = "S0"
    if previous_state in CANONICAL_STATES and state in CANONICAL_STATES:
        prev_idx = CANONICAL_STATES.index(previous_state)
        target_idx = CANONICAL_STATES.index(state)
        allow_skip = _is_valid_transition_path(previous_state, state, decision_json.get("state_transition_path"))
        if target_idx - prev_idx > 1 and not allow_skip:
            state = CANONICAL_STATES[prev_idx + 1]
            decision_json["state"] = state
            decision_json["state_code"] = state
            decision_json["state_label"] = _state_label(state)
            decision_json["approval_required"] = True
            decision_json["approval_checkpoint_required"] = True
            if str(decision_json.get("status_gate") or "PENDING").upper() == "PASS":
                decision_json["status_gate"] = "NEEDS_APPROVAL"
            reasons = _as_list_of_str(decision_json.get("rule_explanations"))
            reasons.append(f"state progression guard applied: {previous_state}->{state}")
            decision_json["rule_explanations"] = reasons
    row.state = state
    row.state_code = state
    row.state_label = str(decision_json.get("state_label") or _state_label(state))
    row.status_gate = str(decision_json.get("status_gate") or "PENDING").upper()
    row.approval_required = bool(decision_json.get("approval_required"))
    row.rule_version = str(decision_json.get("rule_version") or RULE_VERSION_FALLBACK)
    row.mode = _normalize_mode(decision_json.get("mode"))
    row.confidence = _clamp_confidence(decision_json.get("confidence"), 0.05)
    row.risk_flags = decision_json.get("risk_flags") if isinstance(decision_json.get("risk_flags"), list) else []
    row.decision_json = decision_json if isinstance(decision_json, dict) else {}
    explanations = _as_list_of_str(decision_json.get("rule_explanations"))
    row.notes = "; ".join(explanations[:6]) if explanations else None
    return row
