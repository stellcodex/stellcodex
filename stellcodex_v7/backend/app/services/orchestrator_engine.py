from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.file import UploadFile
from app.models.orchestrator import OrchestratorSession, RuleConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


REQUIRED_RULE_CONFIG_KEYS: tuple[str, ...] = (
    "draft_min_deg",
    "wall_mm_min",
    "wall_mm_max",
    "block_on_unknown_critical",
    "force_approval_on_visual_only",
    "allow_hot_runner",
)

RULE_CONFIG_DESCRIPTIONS: dict[str, str] = {
    "draft_min_deg": "Minimum draft angle in degrees",
    "wall_mm_min": "Minimum wall thickness (mm)",
    "wall_mm_max": "Maximum wall thickness (mm)",
    "block_on_unknown_critical": "Block auto-approval if critical geometry fields are unknown",
    "force_approval_on_visual_only": "Visual-only mode requires manual approval",
    "allow_hot_runner": "Hot runner disabled by default",
}

RULE_CONFIG_BOOTSTRAP_PATH = Path(__file__).with_name("rule_config_bootstrap.json")


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
        if row is not None:
            continue
        row = RuleConfig(
            key=key,
            value_json={"value": bootstrap_values[key]},
            enabled=True,
            description=RULE_CONFIG_DESCRIPTIONS.get(key),
        )
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
        raise RuntimeError(
            f"Missing required enabled rule_configs: {missing}"
        )
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
    return [str(item) for item in raw]


def _status_to_base_state(status: str) -> tuple[str, str]:
    token = (status or "").strip().lower()
    if token in {"pending", ""}:
        return "S0", "uploaded"
    if token in {"queued"}:
        return "S1", "queued"
    if token in {"running", "processing"}:
        return "S2", "processing"
    if token in {"failed"}:
        return "S7", "rejected"
    if token in {"ready", "succeeded"}:
        return "S4", "dfm_ready"
    return "S3", "artifacts_generated"


def build_decision_json(file_row: UploadFile, rules: dict[str, Any]) -> dict[str, Any]:
    draft_min_deg = _rule_as_float(rules, "draft_min_deg")
    wall_mm_min = _rule_as_float(rules, "wall_mm_min")
    wall_mm_max = _rule_as_float(rules, "wall_mm_max")
    block_on_unknown_critical = _rule_as_bool(rules, "block_on_unknown_critical")
    force_approval_on_visual_only = _rule_as_bool(rules, "force_approval_on_visual_only")
    allow_hot_runner = _rule_as_bool(rules, "allow_hot_runner")

    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    kind = str(meta.get("kind") or "3d").strip().lower()
    mode = str(meta.get("mode") or "brep").strip().lower()

    state_code, state_label = _status_to_base_state(file_row.status)
    status_gate = "PENDING"
    risk_flags: list[str] = []
    reasons: list[str] = []

    if state_code == "S7":
        status_gate = "REJECTED"
        reasons.append("file_processing_failed")

    if kind != "3d" and state_code not in {"S7", "S0", "S1", "S2"}:
        status_gate = "PASS"
        state_code, state_label = "S6", "approved_ready"
        reasons.append("non_3d_auto_pass")
    elif kind == "3d" and state_code not in {"S7", "S0", "S1", "S2"}:
        dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else {}
        geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}
        critical_unknowns = _as_list_of_str(geometry_report.get("critical_unknowns"))

        raw_gate = str(dfm_findings.get("status_gate") or "PASS").strip().upper()
        status_gate = raw_gate if raw_gate in {"PASS", "NEEDS_APPROVAL", "REJECTED"} else "PASS"
        risk_flags.extend(_as_list_of_str(dfm_findings.get("risk_flags")))

        if block_on_unknown_critical and critical_unknowns:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("unknown_critical_geometry")
            reasons.append("critical_geometry_unknown")

        if mode == "visual_only" and force_approval_on_visual_only:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("visual_only_mode")
            reasons.append("visual_only_requires_manual_approval")

        runner_mode = str(dfm_findings.get("runner_mode") or "").strip().lower()
        if runner_mode == "hot" and not allow_hot_runner:
            status_gate = "NEEDS_APPROVAL"
            risk_flags.append("hot_runner_requested")
            reasons.append("hot_runner_disallowed_by_rule")

        if status_gate == "PASS":
            state_code, state_label = "S6", "approved_ready"
        elif status_gate == "NEEDS_APPROVAL":
            state_code, state_label = "S5", "needs_approval"
        elif status_gate == "REJECTED":
            state_code, state_label = "S7", "rejected"

    decision = "manual_review"
    if state_code == "S6":
        decision = "approve_auto"
    elif state_code == "S7":
        decision = "reject"

    risk_flags = sorted({item for item in risk_flags if item})
    approval_required = state_code in {"S5", "S7"}

    return {
        "schema": "stellcodex.v7.decision_json",
        "version": "1.0",
        "state_code": state_code,
        "state_label": state_label,
        "status_gate": status_gate,
        "decision": decision,
        "approval_required": approval_required,
        "risk_flags": risk_flags,
        "reasons": reasons,
        "thresholds": {
            "draft_min_deg": draft_min_deg,
            "wall_mm_min": wall_mm_min,
            "wall_mm_max": wall_mm_max,
            "block_on_unknown_critical": block_on_unknown_critical,
            "force_approval_on_visual_only": force_approval_on_visual_only,
            "allow_hot_runner": allow_hot_runner,
        },
        "file_id": file_row.file_id,
        "updated_at": _now_iso(),
    }


def upsert_orchestrator_session(db: Session, file_row: UploadFile, decision_json: dict[str, Any]) -> OrchestratorSession:
    row = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()
    if row is None:
        row = OrchestratorSession(file_id=file_row.file_id)
        db.add(row)

    row.state_code = str(decision_json.get("state_code") or "S0")
    row.state_label = str(decision_json.get("state_label") or "uploaded")
    row.status_gate = str(decision_json.get("status_gate") or "PENDING")
    row.approval_required = bool(decision_json.get("approval_required"))
    row.risk_flags = decision_json.get("risk_flags") if isinstance(decision_json.get("risk_flags"), list) else []
    row.decision_json = decision_json
    row.notes = ", ".join(_as_list_of_str(decision_json.get("reasons")))
    return row
