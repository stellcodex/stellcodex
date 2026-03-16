from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.orchestrator import OrchestratorSession
from app.services.mfg_classifier import classify_manufacturing_process

STATE_DEFS: dict[str, dict[str, str]] = {
    "S0": {"legacy": "S0 Uploaded", "slug": "uploaded", "label": "Uploaded"},
    "S1": {"legacy": "S1 Converted", "slug": "converted", "label": "Converted"},
    "S2": {"legacy": "S2 AssemblyReady", "slug": "assembly_ready", "label": "Assembly Ready"},
    "S3": {"legacy": "S3 Analyzing", "slug": "analyzing", "label": "Analyzing"},
    "S4": {"legacy": "S4 DFMReady", "slug": "dfm_ready", "label": "DFM Ready"},
    "S5": {"legacy": "S5 AwaitingApproval", "slug": "awaiting_approval", "label": "Awaiting Approval"},
    "S6": {"legacy": "S6 Approved", "slug": "approved", "label": "Approved"},
    "S7": {"legacy": "S7 ShareReady", "slug": "share_ready", "label": "Share Ready"},
}


def normalize_state_code(state: str | None) -> str:
    token = str(state or "").strip()
    if token in STATE_DEFS:
        return token

    lowered = token.lower()
    for code, meta in STATE_DEFS.items():
        if token == meta["legacy"] or lowered == meta["slug"] or lowered == meta["label"].lower():
            return code

    return "S0"


def normalize_decision_mode(mode: str | None) -> str:
    token = str(mode or "").strip().lower()
    if token == "brep":
        return "brep"
    if token == "mesh_approx":
        return "mesh_approx"
    return "visual_only"


def state_label(state: str | None) -> str:
    code = normalize_state_code(state)
    return STATE_DEFS.get(code, {}).get("label", str(state or "Unknown"))


def state_slug(state: str | None) -> str:
    code = normalize_state_code(state)
    return STATE_DEFS.get(code, {}).get("slug", "uploaded")


def approval_required(
    decision_json: dict[str, Any] | None,
    dfm_findings: dict[str, Any] | None = None,
) -> bool:
    payload = decision_json if isinstance(decision_json, dict) else {}
    flags = payload.get("conflict_flags")
    if isinstance(flags, list) and flags:
        return True
    if isinstance(dfm_findings, dict):
        return str(dfm_findings.get("status_gate") or "").strip().upper() == "NEEDS_APPROVAL"
    return False


def session_risk_flags(decision_json: dict[str, Any] | None) -> list[str]:
    payload = decision_json if isinstance(decision_json, dict) else {}
    flags = payload.get("conflict_flags")
    if not isinstance(flags, list):
        return []
    return [str(item) for item in flags if str(item).strip()]


def apply_session_state(
    session: OrchestratorSession,
    *,
    state: str,
    decision_json: dict[str, Any] | None,
) -> OrchestratorSession:
    code = normalize_state_code(state)
    needs_approval = approval_required(decision_json)
    session.state = code
    session.state_code = code
    session.state_label = state_slug(code)
    session.approval_required = needs_approval
    session.status_gate = "NEEDS_APPROVAL" if needs_approval else "PASS"
    session.risk_flags = session_risk_flags(decision_json)
    return session


def _severity_for_decision(value: Any) -> str:
    token = str(value or "").strip().lower()
    if token in {"blocking", "high"}:
        return "HIGH"
    if token in {"warning", "medium"}:
        return "MEDIUM"
    if token == "low":
        return "LOW"
    return "INFO"


def _manufacturing_method_from_process(process: str) -> str:
    token = str(process or "").strip().lower()
    if token in {"cnc_turning", "cnc_milling"}:
        return "cnc"
    if token == "3d_printing":
        return "3d_printing"
    return "unknown"


def build_decision_json(
    *,
    mode: str | None,
    rule_version: str,
    geometry_meta: dict[str, Any] | None = None,
    dfm_findings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_decision_mode(mode)
    geometry = geometry_meta if isinstance(geometry_meta, dict) else {}
    findings = dfm_findings.get("findings") if isinstance(dfm_findings, dict) else None
    risk_flags = dfm_findings.get("risk_flags") if isinstance(dfm_findings, dict) else None

    process = classify_manufacturing_process(geometry)
    confidence = float(process.confidence or 0.0)
    if normalized_mode == "visual_only" and not geometry:
        confidence = 0.0
    elif normalized_mode == "visual_only":
        confidence = min(max(confidence, 0.1), 0.5)
    else:
        confidence = min(max(confidence, 0.1), 1.0)

    explanations: list[dict[str, Any]] = []
    if isinstance(findings, list):
        for item in findings:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "RULE").strip().upper()
            message = str(item.get("message") or "Deterministic rule triggered.").strip()
            explanations.append(
                {
                    "rule_id": code,
                    "triggered": True,
                    "severity": _severity_for_decision(item.get("severity")),
                    "reference": f"rule_configs:{code.lower()}",
                    "reasoning": message or "Deterministic rule triggered.",
                }
            )

    if not explanations:
        explanations.append(
            {
                "rule_id": "R00_DEFAULT",
                "triggered": False,
                "severity": "INFO",
                "reference": "rule_configs:default",
                "reasoning": "Deterministic fallback applied because no explicit blocking rule was triggered.",
            }
        )

    return {
        "rule_version": str(rule_version or "v0.0"),
        "mode": normalized_mode,
        "confidence": round(confidence, 4),
        "manufacturing_method": _manufacturing_method_from_process(process.process),
        "rule_explanations": explanations,
        "conflict_flags": [str(item) for item in risk_flags] if isinstance(risk_flags, list) else [],
    }


def derive_session_state(
    *,
    file_status: str,
    kind: str,
    decision_json: dict[str, Any] | None,
    dfm_findings: dict[str, Any] | None = None,
    current_state: str | None = None,
) -> str:
    state = normalize_state_code(current_state)
    if state in {"S6", "S7"}:
        return state
    if str(file_status or "").strip().lower() != "ready":
        return state or "S0"
    if approval_required(decision_json, dfm_findings):
        return "S5"
    if kind == "3d":
        return "S4"
    return "S1"


def upsert_orchestrator_session(
    db: Session,
    *,
    file_id: str,
    state: str,
    decision_json: dict[str, Any],
    rule_version: str,
    mode: str | None,
) -> OrchestratorSession | None:
    try:
        session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_id).first()
        normalized_mode = normalize_decision_mode(mode or decision_json.get("mode"))
        confidence = float(decision_json.get("confidence") or 0.0)

        if session is None:
            session = OrchestratorSession(
                file_id=file_id,
                decision_json=decision_json,
                rule_version=str(rule_version or decision_json.get("rule_version") or "v0.0"),
                mode=normalized_mode,
                confidence=confidence,
            )
        else:
            session.decision_json = decision_json
            session.rule_version = str(rule_version or decision_json.get("rule_version") or session.rule_version or "v0.0")
            session.mode = normalized_mode
            session.confidence = confidence

        apply_session_state(session, state=state, decision_json=decision_json)
        db.add(session)
        return session
    except Exception:
        return None
