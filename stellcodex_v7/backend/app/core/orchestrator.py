from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.dfm_engine import build_dfm_pdf, build_dfm_report
from app.core.rule_engine import evaluate_deterministic_rules, summarize_triggered_rules
from app.models.file import UploadFile
from app.models.orchestrator import OrchestratorSession
from app.services.audit import log_event
from app.services.orchestrator_engine import (
    CANONICAL_STATES,
    build_decision_json,
    load_rule_config_map,
    normalize_decision_json,
    upsert_orchestrator_session,
)

STATE_INDEX = {state: idx for idx, state in enumerate(CANONICAL_STATES)}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_meta(file_row: UploadFile) -> dict[str, Any]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    if not isinstance(file_row.meta, dict):
        file_row.meta = meta
    return meta


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def classify_input(input_text: str | None, payload: dict[str, Any] | None) -> dict[str, Any]:
    raw_text = _as_text(input_text).lower()
    data = payload if isinstance(payload, dict) else {}
    detected: list[str] = []
    if "qty" in raw_text or "quantity" in raw_text or any(k in data for k in ("qty", "quantity", "requested_quantity")):
        detected.append("quantity")
    if "tolerance" in raw_text or any(k in data for k in ("tolerance_mm", "tolerance")):
        detected.append("tolerance_mm")
    if "material" in raw_text or "shrink" in raw_text or any(k in data for k in ("material", "material_shrinkage_pct")):
        detected.append("material")
    if "approve" in raw_text:
        detected.append("approval_intent")
    return {
        "received_at": _now_iso(),
        "detected_fields": sorted(set(detected)),
        "input_text": input_text,
        "payload": data,
    }


def request_required_inputs(file_row: UploadFile, decision_json: dict[str, Any]) -> list[str]:
    meta = _ensure_meta(file_row)
    mode = str(decision_json.get("mode") or meta.get("mode") or "visual_only")
    required: list[str] = []
    if "quantity" not in meta and "requested_quantity" not in meta:
        required.append("quantity")
    if mode != "visual_only" and "tolerance_mm" not in meta:
        required.append("tolerance_mm")
    if "material" not in meta and "material_shrinkage_pct" not in meta:
        required.append("material")
    return required


def _state_label(state: str) -> str:
    labels = {
        "S0": "uploaded",
        "S1": "converted",
        "S2": "assembly_ready",
        "S3": "analyzing",
        "S4": "dfm_ready",
        "S5": "awaiting_approval",
        "S6": "approved",
        "S7": "share_ready",
    }
    return labels.get(state, "uploaded")


def enforce_state_machine(previous_state: str | None, target_state: str) -> tuple[str, list[str], bool]:
    if target_state not in STATE_INDEX:
        return "S0", ["S0"], False
    if previous_state not in STATE_INDEX:
        return target_state, [target_state], False
    prev_idx = STATE_INDEX[previous_state]
    target_idx = STATE_INDEX[target_state]

    if target_idx <= prev_idx:
        return target_state, [previous_state, target_state], False

    # Strict progression: advance one step at a time for existing sessions.
    if target_idx - prev_idx > 1:
        bounded = CANONICAL_STATES[prev_idx + 1]
        return bounded, [previous_state, bounded], True
    return target_state, [previous_state, target_state], False


def _decision_hash(decision_json: dict[str, Any]) -> str:
    payload = json.dumps(decision_json, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _merge_rule_outputs(decision_json: dict[str, Any], rule_results: list[dict[str, Any]]) -> dict[str, Any]:
    out = dict(decision_json)
    base_risks = [str(item) for item in (out.get("risk_flags") or []) if str(item).strip()]
    base_conflicts = [str(item) for item in (out.get("conflict_flags") or []) if str(item).strip()]
    base_reasons = [str(item) for item in (out.get("rule_explanations") or []) if str(item).strip()]

    extra_risks, extra_conflicts, extra_reasons = summarize_triggered_rules(rule_results)
    out["risk_flags"] = sorted(set(base_risks + extra_risks))
    out["conflict_flags"] = sorted(set(base_conflicts + extra_conflicts))

    merged_reasons = base_reasons + extra_reasons
    dedup_reasons: list[str] = []
    seen: set[str] = set()
    for item in merged_reasons:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        dedup_reasons.append(key)
    out["rule_explanations"] = dedup_reasons
    out["deterministic_rules"] = rule_results
    return out


def _evidence_payload(
    *,
    file_id: str,
    session_id: str,
    decision_json: dict[str, Any],
    dfm_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "file_id": file_id,
        "rules_fired": [
            str(item.get("rule_id"))
            for item in (decision_json.get("deterministic_rules") or [])
            if isinstance(item, dict) and item.get("triggered")
        ],
        "risks": [str(item) for item in (decision_json.get("risk_flags") or [])],
        "decision_hash": _decision_hash(decision_json),
        "artifact_references": {
            "dfm_report_hash": dfm_report.get("report_hash"),
            "dfm_report_schema": dfm_report.get("schema"),
        },
    }


def ensure_session_decision(
    db: Session,
    file_row: UploadFile,
    *,
    input_text: str | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[OrchestratorSession, dict[str, Any]]:
    rules = load_rule_config_map(db)
    current_row = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()

    base_decision = normalize_decision_json(
        file_row,
        rules,
        (current_row.decision_json if current_row is not None else file_row.decision_json) or build_decision_json(file_row, rules),
    )

    meta = _ensure_meta(file_row)
    if input_text is not None or payload is not None:
        input_entry = classify_input(input_text, payload)
        history = meta.get("orchestrator_inputs")
        if not isinstance(history, list):
            history = []
        history.append(input_entry)
        meta["orchestrator_inputs"] = history[-20:]
        for key in ("quantity", "requested_quantity", "qty", "tolerance_mm", "material", "material_shrinkage_pct"):
            if key in (payload or {}):
                meta[key] = (payload or {}).get(key)

    rule_results = evaluate_deterministic_rules(meta, rules)
    merged_decision = _merge_rule_outputs(base_decision, rule_results)

    required_inputs = request_required_inputs(file_row, merged_decision)
    manual_override = str(meta.get("approval_override") or "").strip().lower()
    manual_decision = str(merged_decision.get("decision") or "").strip().lower()
    manual_approved = manual_override == "approved" or manual_decision in {"approve_manual", "approved_manual"}
    if required_inputs and merged_decision.get("state") in {"S6", "S7"} and not manual_approved:
        merged_decision["state"] = "S5"
        merged_decision["state_code"] = "S5"
        merged_decision["state_label"] = _state_label("S5")
        merged_decision["status_gate"] = "NEEDS_APPROVAL"
        merged_decision["approval_required"] = True
        reasons = [str(item) for item in (merged_decision.get("rule_explanations") or [])]
        reasons.append(f"required_inputs_pending: {', '.join(required_inputs)}")
        merged_decision["rule_explanations"] = reasons
    elif required_inputs and manual_approved:
        reasons = [str(item) for item in (merged_decision.get("rule_explanations") or [])]
        marker = f"required_inputs_acknowledged_by_manual_approval: {', '.join(required_inputs)}"
        if marker not in reasons:
            reasons.append(marker)
        merged_decision["rule_explanations"] = reasons
        merged_decision["status_gate"] = "PASS"
        merged_decision["approval_required"] = False
    merged_decision["required_inputs"] = required_inputs

    previous_state = str(current_row.state) if current_row is not None else None
    target_state = str(merged_decision.get("state") or merged_decision.get("state_code") or "S0")
    bounded_state, transition_path, checkpoint_required = enforce_state_machine(previous_state, target_state)
    if bounded_state != target_state:
        merged_decision["state"] = bounded_state
        merged_decision["state_code"] = bounded_state
        merged_decision["state_label"] = _state_label(bounded_state)
        merged_decision["approval_required"] = True
        if str(merged_decision.get("status_gate")).upper() == "PASS":
            merged_decision["status_gate"] = "NEEDS_APPROVAL"
    merged_decision["state_transition_path"] = transition_path
    merged_decision["approval_checkpoint_required"] = checkpoint_required
    merged_decision["updated_at"] = _now_iso()

    dfm_report = build_dfm_report(file_row, rules, merged_decision, rule_results)
    dfm_pdf = build_dfm_pdf(dfm_report)

    meta["decision_json"] = merged_decision
    meta["dfm_report_json"] = dfm_report
    meta["dfm_report_hash"] = str(dfm_report.get("report_hash"))
    meta["dfm_report_pdf_b64"] = base64.b64encode(dfm_pdf).decode("ascii")
    meta["dfm_report_generated_at"] = _now_iso()
    file_row.meta = {**meta}
    file_row.decision_json = merged_decision
    db.add(file_row)
    if hasattr(file_row, "_sa_instance_state"):
        flag_modified(file_row, "meta")

    row = upsert_orchestrator_session(db, file_row, merged_decision)
    db.add(row)
    db.flush()

    log_event(
        db,
        "orchestrator.decision_generated",
        file_id=file_row.file_id,
        data=_evidence_payload(
            file_id=file_row.file_id,
            session_id=str(row.id),
            decision_json=merged_decision,
            dfm_report=dfm_report,
        ),
    )
    db.commit()
    db.refresh(row)
    return row, merged_decision
