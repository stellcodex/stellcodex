from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_learning import (
    AiCaseLog,
    AiEvalResult,
    AiPatternSignal,
    BlockedCase,
    FailedCase,
    RecoveredCase,
    SolvedCase,
)
from app.models.file import UploadFile as UploadFileModel
from app.services.ai_snapshot_jobs import (
    SNAPSHOT_STATUS_QUEUED,
    SnapshotEnqueueError,
    create_snapshot_job,
    enqueue_snapshot_upload_job,
    mark_snapshot_retry_pending,
    write_local_snapshot,
)

FINAL_STATUSES = {"success", "failure", "blocked"}
MEMORY_TABLE_BY_TYPE = {
    "solved": SolvedCase,
    "failed": FailedCase,
    "blocked": BlockedCase,
    "recovered": RecoveredCase,
}
SIGNAL_TYPES = {"pattern_signal", "recovery_signal", "optimization_signal"}
REPEAT_FAILURE_GUARD = "repeat_failure_guard"
NON_SIGNATURE_FLAGS = {REPEAT_FAILURE_GUARD}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_json(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=True)
        return value
    except Exception:
        if isinstance(value, dict):
            return {str(key): _safe_json(item) for key, item in value.items()}
        if isinstance(value, list):
            return [_safe_json(item) for item in value]
        if value is None:
            return None
        return str(value)


def _normalize_mode(value: Any) -> str:
    token = _safe_text(value).lower()
    if token in {"brep", "mesh_approx", "visual_only"}:
        return token
    return "visual_only"


def _normalized_tokens(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        token = _safe_text(value).lower()
        if not token or token in seen:
            continue
        seen.add(token)
        items.append(token)
    return items


def _file_meta(file_row: UploadFileModel | None) -> dict[str, Any]:
    meta = file_row.meta if file_row is not None and isinstance(file_row.meta, dict) else {}
    return meta if isinstance(meta, dict) else {}


def _project_id(file_row: UploadFileModel, input_payload: dict[str, Any]) -> str:
    context = _safe_dict(input_payload.get("context"))
    token = (
        _safe_text(input_payload.get("project_id"))
        or _safe_text(context.get("project_id"))
        or _safe_text(_file_meta(file_row).get("project_id"))
    )
    return token or "default"


def _geometry_meta(file_row: UploadFileModel, input_payload: dict[str, Any]) -> dict[str, Any]:
    context = _safe_dict(input_payload.get("context"))
    value = _safe_dict(input_payload.get("geometry_meta"))
    if value:
        return value
    value = _safe_dict(context.get("geometry_meta"))
    if value:
        return value
    return _safe_dict(_file_meta(file_row).get("geometry_meta_json"))


def _dfm_findings(file_row: UploadFileModel, input_payload: dict[str, Any]) -> dict[str, Any]:
    context = _safe_dict(input_payload.get("context"))
    value = _safe_dict(input_payload.get("dfm_findings"))
    if value:
        return value
    value = _safe_dict(context.get("dfm_findings"))
    if value:
        return value
    return _safe_dict(_file_meta(file_row).get("dfm_findings"))


def _finding_codes(dfm_findings: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for item in _safe_list(dfm_findings.get("findings")):
        if not isinstance(item, dict):
            continue
        code = _safe_text(item.get("code")).upper()
        if code:
            items.append(code)
    return _normalized_tokens(items)


def _risk_flags(decision_output: dict[str, Any], dfm_findings: dict[str, Any]) -> list[str]:
    return [
        token
        for token in _normalized_tokens(
            _safe_list(decision_output.get("conflict_flags")) + _safe_list(dfm_findings.get("risk_flags"))
        )
        if token not in NON_SIGNATURE_FLAGS
    ]


def _status_gate(dfm_findings: dict[str, Any], input_payload: dict[str, Any]) -> str:
    blocked_reasons = _safe_list(input_payload.get("blocked_reasons"))
    if blocked_reasons:
        for item in blocked_reasons:
            if not isinstance(item, dict):
                continue
            code = _safe_text(item.get("code")).lower()
            if code == "missing_required_inputs":
                return "NEEDS_INPUT"
            if code == "approval_required":
                return "NEEDS_APPROVAL"
    token = _safe_text(dfm_findings.get("status_gate")).upper()
    return token or "UNKNOWN"


def _failure_class(
    *,
    final_status: str,
    run_type: str,
    input_payload: dict[str, Any],
    error_trace: dict[str, Any] | None,
) -> str | None:
    if final_status != "failure":
        return None
    blocked_reasons = _safe_list(input_payload.get("blocked_reasons"))
    if any(_safe_text(_safe_dict(item).get("code")).lower() == "missing_required_inputs" for item in blocked_reasons):
        return "missing_input"

    trace = _safe_dict(error_trace)
    message = " ".join(
        [
            _safe_text(trace.get("message")),
            _safe_text(trace.get("detail")),
            _safe_text(trace.get("source")),
            _safe_text(trace.get("type")),
            _safe_text(run_type),
        ]
    ).lower()
    if any(token in message for token in ["connection", "timeout", "unavailable", "dns", "refused", "network", "503"]):
        return "infra_error"
    if any(token in message for token in ["stell.ai", "decision", "rule config", "invalid decision"]):
        return "decision_error"
    if any(token in message for token in ["input", "required input", "missing input"]):
        return "missing_input"
    return "execution_error"


def _problem_signature(
    *,
    file_row: UploadFileModel,
    input_payload: dict[str, Any],
    decision_output: dict[str, Any],
    failure_class: str | None,
) -> tuple[str, str, dict[str, Any]]:
    meta = _file_meta(file_row)
    geometry = _geometry_meta(file_row, input_payload)
    dfm_findings = _dfm_findings(file_row, input_payload)
    flags = _risk_flags(decision_output, dfm_findings)
    finding_codes = _finding_codes(dfm_findings)
    payload = {
        "project_id": _project_id(file_row, input_payload),
        "kind": _safe_text(meta.get("kind")) or "3d",
        "mode": _normalize_mode(
            input_payload.get("mode") or decision_output.get("mode") or meta.get("mode")
        ),
        "status_gate": _status_gate(dfm_findings, input_payload),
        "manufacturing_method": _safe_text(decision_output.get("manufacturing_method")) or "unknown",
        "has_geometry": bool(geometry),
        "part_count": geometry.get("part_count") if isinstance(geometry.get("part_count"), int) else meta.get("part_count"),
        "risk_flags": flags,
        "finding_codes": finding_codes,
        "failure_class": _safe_text(failure_class) or None,
    }
    normalized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    similarity_key = "|".join(
        [
            str(payload["project_id"]),
            str(payload["kind"]),
            str(payload["mode"]),
            str(payload["status_gate"]),
            ",".join(flags[:3]) or "none",
        ]
    )
    return normalized, similarity_key, payload


def _snapshot_payload(
    *,
    case_log: AiCaseLog,
    input_payload: dict[str, Any],
    signature_payload: dict[str, Any],
    evaluation: dict[str, Any],
    signals: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "case_id": str(case_log.case_id),
        "tenant_id": int(case_log.tenant_id),
        "file_id": case_log.file_id,
        "project_id": case_log.project_id,
        "session_id": case_log.session_id,
        "run_type": case_log.run_type,
        "normalized_problem_signature": case_log.normalized_problem_signature,
        "similarity_index_key": case_log.similarity_index_key,
        "input_payload": _safe_json(input_payload),
        "decision_output": _safe_json(case_log.decision_output),
        "execution_trace": _safe_json(case_log.execution_trace),
        "final_status": case_log.final_status,
        "error_trace": _safe_json(case_log.error_trace),
        "duration_ms": int(case_log.duration_ms or 0),
        "timestamp": case_log.created_at.isoformat() if case_log.created_at else _now().isoformat(),
        "signature_context": signature_payload,
        "eval_result": evaluation,
        "signals": signals,
    }


def _evaluation_summary(history: list[AiCaseLog], case_log: AiCaseLog, failure_class: str | None) -> tuple[dict[str, Any], float, float]:
    similar = [item for item in history if item.similarity_index_key == case_log.similarity_index_key]
    if not similar:
        similar = history
    total = len(similar)
    success_count = sum(1 for item in similar if item.final_status == "success")
    durations = [float(item.duration_ms or 0) / 1000.0 for item in similar if item.duration_ms is not None]
    failure_counts = Counter(_safe_text(item.failure_class) or "none" for item in similar if item.final_status == "failure")
    success_rate = round(success_count / total, 4) if total else 0.0
    average_resolution_seconds = round(mean(durations), 4) if durations else 0.0
    evaluation = {
        "case_id": str(case_log.case_id),
        "outcome": case_log.final_status,
        "failure_class": failure_class,
        "success_rate": success_rate,
        "average_resolution_seconds": average_resolution_seconds,
        "similar_case_count": total,
        "failure_patterns": [
            {"failure_class": key, "count": value}
            for key, value in failure_counts.most_common()
            if key != "none"
        ],
    }
    return evaluation, success_rate, average_resolution_seconds


def _memory_outcome(case_log: AiCaseLog, failure_class: str | None) -> dict[str, Any]:
    return {
        "final_status": case_log.final_status,
        "failure_class": failure_class,
        "duration_ms": int(case_log.duration_ms or 0),
        "run_type": case_log.run_type,
        "drive_snapshot_status": case_log.drive_snapshot_status,
        "created_at": case_log.created_at.isoformat() if case_log.created_at else _now().isoformat(),
        "decision_confidence": float(_safe_dict(case_log.decision_output).get("confidence") or 0.0),
        "manufacturing_method": _safe_text(_safe_dict(case_log.decision_output).get("manufacturing_method")) or "unknown",
    }


def _store_memory_case(
    db: Session,
    table_model: type[SolvedCase] | type[FailedCase] | type[BlockedCase] | type[RecoveredCase],
    *,
    case_log: AiCaseLog,
    outcome: dict[str, Any],
) -> None:
    row = db.get(table_model, case_log.case_id)
    if row is None:
        row = table_model(case_id=case_log.case_id)
    row.tenant_id = case_log.tenant_id
    row.file_id = case_log.file_id
    row.project_id = case_log.project_id
    row.normalized_problem_signature = case_log.normalized_problem_signature
    row.similarity_index_key = case_log.similarity_index_key
    row.decision_taken = case_log.decision_output if isinstance(case_log.decision_output, dict) else {}
    row.outcome = outcome
    row.created_at = case_log.created_at
    db.add(row)


def _upsert_signal(
    db: Session,
    *,
    tenant_id: int,
    signal_type: str,
    normalized_problem_signature: str,
    similarity_index_key: str,
    failure_class: str | None,
    payload: dict[str, Any],
) -> AiPatternSignal:
    signal = (
        db.query(AiPatternSignal)
        .filter(
            AiPatternSignal.tenant_id == tenant_id,
            AiPatternSignal.signal_type == signal_type,
            AiPatternSignal.similarity_index_key == similarity_index_key,
            AiPatternSignal.failure_class == failure_class,
            AiPatternSignal.active.is_(True),
        )
        .order_by(AiPatternSignal.created_at.desc())
        .first()
    )
    if signal is None:
        signal = AiPatternSignal(
            tenant_id=tenant_id,
            signal_type=signal_type,
            normalized_problem_signature=normalized_problem_signature,
            similarity_index_key=similarity_index_key,
            failure_class=failure_class,
        )
    signal.signal_payload = payload
    signal.active = True
    signal.updated_at = _now()
    db.add(signal)
    db.flush()
    return signal


def _serialize_signal(signal: AiPatternSignal) -> dict[str, Any]:
    return {
        "signal_id": str(signal.signal_id),
        "signal_type": signal.signal_type,
        "similarity_index_key": signal.similarity_index_key,
        "failure_class": signal.failure_class,
        "signal_payload": signal.signal_payload if isinstance(signal.signal_payload, dict) else {},
        "active": bool(signal.active),
        "created_at": signal.created_at.isoformat() if signal.created_at else None,
        "updated_at": signal.updated_at.isoformat() if signal.updated_at else None,
    }


def _refresh_signals(db: Session, *, case_log: AiCaseLog, failure_class: str | None) -> list[dict[str, Any]]:
    signals: list[AiPatternSignal] = []

    if case_log.final_status == "failure" and failure_class:
        repeated = (
            db.query(AiCaseLog)
            .filter(
                AiCaseLog.tenant_id == case_log.tenant_id,
                AiCaseLog.similarity_index_key == case_log.similarity_index_key,
                AiCaseLog.final_status == "failure",
                AiCaseLog.failure_class == failure_class,
            )
            .count()
        )
        if repeated >= 3:
            signals.append(
                _upsert_signal(
                    db,
                    tenant_id=case_log.tenant_id,
                    signal_type="pattern_signal",
                    normalized_problem_signature=case_log.normalized_problem_signature,
                    similarity_index_key=case_log.similarity_index_key,
                    failure_class=failure_class,
                    payload={
                        "repeat_count": repeated,
                        "guard_flag": REPEAT_FAILURE_GUARD,
                        "recommended_action": "Require recovery plan input before automatic advance.",
                    },
                )
            )

    if case_log.final_status == "success":
        previous_failures = (
            db.query(AiCaseLog)
            .filter(
                AiCaseLog.tenant_id == case_log.tenant_id,
                AiCaseLog.similarity_index_key == case_log.similarity_index_key,
                AiCaseLog.case_id != case_log.case_id,
                AiCaseLog.final_status.in_(("failure", "blocked")),
            )
            .count()
        )
        if previous_failures:
            signals.append(
                _upsert_signal(
                    db,
                    tenant_id=case_log.tenant_id,
                    signal_type="recovery_signal",
                    normalized_problem_signature=case_log.normalized_problem_signature,
                    similarity_index_key=case_log.similarity_index_key,
                    failure_class=None,
                    payload={
                        "previous_failed_runs": previous_failures,
                        "recovered_case_id": str(case_log.case_id),
                    },
                )
            )

        prior_successes = (
            db.query(AiCaseLog)
            .filter(
                AiCaseLog.tenant_id == case_log.tenant_id,
                AiCaseLog.similarity_index_key == case_log.similarity_index_key,
                AiCaseLog.case_id != case_log.case_id,
                AiCaseLog.final_status == "success",
            )
            .order_by(AiCaseLog.duration_ms.asc())
            .all()
        )
        if prior_successes:
            fastest_prior = min(int(item.duration_ms or 0) for item in prior_successes)
            if fastest_prior > 0 and int(case_log.duration_ms or 0) < int(fastest_prior * 0.9):
                signals.append(
                    _upsert_signal(
                        db,
                        tenant_id=case_log.tenant_id,
                        signal_type="optimization_signal",
                        normalized_problem_signature=case_log.normalized_problem_signature,
                        similarity_index_key=case_log.similarity_index_key,
                        failure_class=None,
                        payload={
                            "previous_best_duration_ms": fastest_prior,
                            "new_best_duration_ms": int(case_log.duration_ms or 0),
                            "improvement_ratio": round(1 - (int(case_log.duration_ms or 0) / fastest_prior), 4),
                        },
                    )
                )

    return [_serialize_signal(item) for item in signals]


def _active_signal_rows(db: Session, *, tenant_id: int, similarity_index_key: str) -> list[AiPatternSignal]:
    return (
        db.query(AiPatternSignal)
        .filter(
            AiPatternSignal.tenant_id == tenant_id,
            AiPatternSignal.similarity_index_key == similarity_index_key,
            AiPatternSignal.active.is_(True),
        )
        .order_by(AiPatternSignal.updated_at.desc(), AiPatternSignal.created_at.desc())
        .all()
    )


def _sanitized_memory_row(case_type: str, row: Any) -> dict[str, Any]:
    outcome = row.outcome if isinstance(row.outcome, dict) else {}
    decision_taken = row.decision_taken if isinstance(row.decision_taken, dict) else {}
    return {
        "case_id": str(row.case_id),
        "case_type": case_type,
        "file_id": row.file_id,
        "project_id": row.project_id,
        "normalized_problem_signature": row.normalized_problem_signature,
        "similarity_index_key": row.similarity_index_key,
        "outcome": {
            "final_status": outcome.get("final_status"),
            "failure_class": outcome.get("failure_class"),
            "duration_ms": outcome.get("duration_ms"),
            "run_type": outcome.get("run_type"),
            "created_at": outcome.get("created_at"),
        },
        "decision_summary": {
            "mode": decision_taken.get("mode"),
            "confidence": decision_taken.get("confidence"),
            "manufacturing_method": decision_taken.get("manufacturing_method"),
            "conflict_flags": _safe_list(decision_taken.get("conflict_flags")),
        },
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def record_case_run(
    db: Session,
    *,
    file_row: UploadFileModel,
    case_id: str | None,
    session_id: str | None,
    run_type: str,
    input_payload: dict[str, Any] | None,
    decision_output: dict[str, Any] | None,
    execution_trace: list[Any] | None,
    final_status: str,
    error_trace: dict[str, Any] | None,
    duration_ms: int | float | None,
    timestamp: datetime | None = None,
    retrieved_context_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = _safe_text(final_status).lower()
    if status not in FINAL_STATUSES:
        raise ValueError("Invalid final_status")

    input_payload = _safe_dict(input_payload)
    decision_output = _safe_dict(decision_output)
    execution_trace = _safe_list(execution_trace)
    error_trace = _safe_dict(error_trace) if isinstance(error_trace, dict) else None
    failure_class = _failure_class(
        final_status=status,
        run_type=run_type,
        input_payload=input_payload,
        error_trace=error_trace,
    )
    normalized_signature, similarity_index_key, signature_payload = _problem_signature(
        file_row=file_row,
        input_payload=input_payload,
        decision_output=decision_output,
        failure_class=failure_class,
    )
    created_at = timestamp or _now()
    project_id = _project_id(file_row, input_payload)

    case_uuid = UUID(str(case_id)) if case_id else uuid4()
    case_log = AiCaseLog(
        case_id=case_uuid,
        tenant_id=int(file_row.tenant_id),
        file_id=file_row.file_id,
        project_id=project_id,
        session_id=_safe_text(session_id) or None,
        run_type=_safe_text(run_type) or "session_sync",
        normalized_problem_signature=normalized_signature,
        similarity_index_key=similarity_index_key,
        input_payload=_safe_json(input_payload),
        decision_output=_safe_json(decision_output),
        execution_trace=_safe_json(execution_trace),
        final_status=status,
        error_trace=_safe_json(error_trace) if error_trace else None,
        failure_class=failure_class,
        duration_ms=max(int(duration_ms or 0), 0),
        retrieved_context_summary=_safe_json(retrieved_context_summary) if isinstance(retrieved_context_summary, dict) else None,
        created_at=created_at,
    )
    db.add(case_log)
    db.flush()

    history = (
        db.query(AiCaseLog)
        .filter(AiCaseLog.tenant_id == case_log.tenant_id)
        .order_by(AiCaseLog.created_at.desc())
        .limit(200)
        .all()
    )
    evaluation, success_rate, average_resolution_seconds = _evaluation_summary(history, case_log, failure_class)
    eval_row = AiEvalResult(
        case_id=case_log.case_id,
        tenant_id=case_log.tenant_id,
        normalized_problem_signature=case_log.normalized_problem_signature,
        similarity_index_key=case_log.similarity_index_key,
        outcome=case_log.final_status,
        decision_taken=case_log.decision_output,
        evaluation=evaluation,
        failure_class=failure_class,
        resolution_seconds=float(case_log.duration_ms or 0) / 1000.0,
        success_rate=success_rate,
        average_resolution_seconds=average_resolution_seconds,
        created_at=created_at,
    )
    db.add(eval_row)

    signals = _refresh_signals(db, case_log=case_log, failure_class=failure_class)
    snapshot = _snapshot_payload(
        case_log=case_log,
        input_payload=input_payload,
        signature_payload=signature_payload,
        evaluation=evaluation,
        signals=signals,
    )
    local_snapshot_path, _relative_snapshot_key, drive_target_path = write_local_snapshot(
        case_id=str(case_log.case_id),
        created_at=created_at,
        payload=snapshot,
    )
    snapshot_job = create_snapshot_job(
        db,
        case_log=case_log,
        local_snapshot_path=local_snapshot_path,
        drive_target_path=drive_target_path,
    )

    outcome = _memory_outcome(case_log, failure_class)
    if case_log.final_status == "success":
        _store_memory_case(db, SolvedCase, case_log=case_log, outcome=outcome)
    elif case_log.final_status == "failure":
        _store_memory_case(db, FailedCase, case_log=case_log, outcome=outcome)
    else:
        _store_memory_case(db, BlockedCase, case_log=case_log, outcome=outcome)

    has_previous_failure = (
        case_log.final_status == "success"
        and db.query(AiCaseLog)
        .filter(
            AiCaseLog.tenant_id == case_log.tenant_id,
            AiCaseLog.similarity_index_key == case_log.similarity_index_key,
            AiCaseLog.case_id != case_log.case_id,
            AiCaseLog.final_status.in_(("failure", "blocked")),
        )
        .count()
        > 0
    )
    if has_previous_failure:
        _store_memory_case(db, RecoveredCase, case_log=case_log, outcome=outcome)

    db.add(case_log)
    db.commit()
    if snapshot_job.upload_status == SNAPSHOT_STATUS_QUEUED:
        try:
            enqueue_snapshot_upload_job(snapshot_job.snapshot_job_id)
        except Exception as exc:
            mark_snapshot_retry_pending(
                snapshot_job.snapshot_job_id,
                error=f"queue enqueue failed: {exc}",
            )
            db.expire_all()
            case_log = db.get(AiCaseLog, case_log.case_id) or case_log
            raise SnapshotEnqueueError(f"snapshot enqueue failed for case {case_log.case_id}: {exc}")

    db.expire_all()
    case_log = db.get(AiCaseLog, case_log.case_id) or case_log
    return {
        "case_id": str(case_log.case_id),
        "similarity_index_key": case_log.similarity_index_key,
        "normalized_problem_signature": case_log.normalized_problem_signature,
        "final_status": case_log.final_status,
        "failure_class": case_log.failure_class,
        "snapshot_job_id": str(snapshot_job.snapshot_job_id),
        "drive_snapshot_path": case_log.drive_snapshot_path,
        "drive_snapshot_status": case_log.drive_snapshot_status,
        "drive_snapshot_error": case_log.drive_snapshot_error,
        "retrieved_context_summary": case_log.retrieved_context_summary,
        "eval_result": evaluation,
        "signals": signals,
    }


def _memory_rows_for_type(db: Session, case_type: str, limit: int) -> list[dict[str, Any]]:
    model = MEMORY_TABLE_BY_TYPE[case_type]
    rows = db.query(model).order_by(model.created_at.desc()).limit(limit).all()
    return [_sanitized_memory_row(case_type, row) for row in rows]


def list_memory_cases(db: Session, *, case_type: str, limit: int = 20) -> dict[str, Any]:
    token = _safe_text(case_type).lower() or "all"
    if token == "all":
        items: list[dict[str, Any]] = []
        for item_type in ("solved", "failed", "blocked", "recovered"):
            items.extend(_memory_rows_for_type(db, item_type, limit))
        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return {"case_type": "all", "items": items[:limit], "total": len(items)}
    if token not in MEMORY_TABLE_BY_TYPE:
        raise ValueError("Invalid memory case type")
    items = _memory_rows_for_type(db, token, limit)
    return {"case_type": token, "items": items, "total": len(items)}


def get_memory_stats(db: Session) -> dict[str, Any]:
    counts = {
        "solved": db.query(func.count(SolvedCase.case_id)).scalar() or 0,
        "failed": db.query(func.count(FailedCase.case_id)).scalar() or 0,
        "blocked": db.query(func.count(BlockedCase.case_id)).scalar() or 0,
        "recovered": db.query(func.count(RecoveredCase.case_id)).scalar() or 0,
        "total_runs": db.query(func.count(AiCaseLog.case_id)).scalar() or 0,
    }
    latest = (
        db.query(AiCaseLog)
        .order_by(AiCaseLog.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        **counts,
        "latest_runs": [
            {
                "case_id": str(item.case_id),
                "file_id": item.file_id,
                "final_status": item.final_status,
                "failure_class": item.failure_class,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in latest
        ],
    }


def get_eval_summary(db: Session, *, limit: int = 50) -> dict[str, Any]:
    rows = db.query(AiEvalResult).order_by(AiEvalResult.created_at.desc()).limit(limit).all()
    total = len(rows)
    success_count = sum(1 for row in rows if row.outcome == "success")
    avg_resolution = mean([float(row.resolution_seconds or 0.0) for row in rows]) if rows else 0.0
    failure_patterns = Counter(
        _safe_text(row.failure_class) or "none"
        for row in rows
        if row.outcome == "failure"
    )
    return {
        "window_size": total,
        "success_rate": round(success_count / total, 4) if total else 0.0,
        "average_resolution_seconds": round(avg_resolution, 4),
        "failure_patterns": [
            {"failure_class": key, "count": value}
            for key, value in failure_patterns.most_common()
            if key != "none"
        ],
        "items": [
            {
                "case_id": str(row.case_id),
                "outcome": row.outcome,
                "failure_class": row.failure_class,
                "resolution_seconds": row.resolution_seconds,
                "success_rate": row.success_rate,
                "average_resolution_seconds": row.average_resolution_seconds,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


def list_pattern_signals(db: Session, *, limit: int = 20) -> dict[str, Any]:
    signals = (
        db.query(AiPatternSignal)
        .filter(AiPatternSignal.active.is_(True))
        .order_by(AiPatternSignal.updated_at.desc(), AiPatternSignal.created_at.desc())
        .limit(limit)
        .all()
    )
    cluster_rows = (
        db.query(
            AiCaseLog.similarity_index_key,
            func.count(AiCaseLog.case_id).label("case_count"),
            func.max(AiCaseLog.created_at).label("last_seen_at"),
        )
        .group_by(AiCaseLog.similarity_index_key)
        .order_by(func.count(AiCaseLog.case_id).desc(), func.max(AiCaseLog.created_at).desc())
        .limit(limit)
        .all()
    )
    return {
        "signals": [_serialize_signal(item) for item in signals],
        "clusters": [
            {
                "similarity_index_key": row.similarity_index_key,
                "case_count": int(row.case_count or 0),
                "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
            }
            for row in cluster_rows
        ],
    }


def _score_memory_candidate(
    *,
    candidate: dict[str, Any],
    similarity_index_key: str,
    normalized_problem_signature: str,
    mode: str,
    risk_flags: list[str],
) -> float:
    score = 0.0
    if candidate.get("similarity_index_key") == similarity_index_key:
        score += 1.0
    if candidate.get("normalized_problem_signature") == normalized_problem_signature:
        score += 0.6
    outcome = _safe_dict(candidate.get("outcome"))
    decision = _safe_dict(candidate.get("decision_summary"))
    if _normalize_mode(decision.get("mode")) == mode:
        score += 0.2
    overlap = len(set(_normalized_tokens(risk_flags)) & set(_normalized_tokens(decision.get("conflict_flags") or [])))
    score += min(overlap * 0.1, 0.3)
    if candidate.get("case_type") == "recovered":
        score += 0.15
    if outcome.get("final_status") == "success":
        score += 0.05
    return round(score, 4)


def get_memory_context(
    db: Session,
    *,
    file_row: UploadFileModel,
    project_id: str | None,
    mode: str | None,
    geometry_meta: dict[str, Any] | None,
    dfm_findings: dict[str, Any] | None,
) -> dict[str, Any]:
    input_payload = {
        "project_id": project_id,
        "mode": mode,
        "geometry_meta": _safe_dict(geometry_meta),
        "dfm_findings": _safe_dict(dfm_findings),
    }
    normalized_signature, similarity_index_key, signature_payload = _problem_signature(
        file_row=file_row,
        input_payload=input_payload,
        decision_output={},
        failure_class=None,
    )
    tenant_cases: list[dict[str, Any]] = []
    for case_type, model in MEMORY_TABLE_BY_TYPE.items():
        rows = (
            db.query(model)
            .filter(model.tenant_id == int(file_row.tenant_id))
            .order_by(model.created_at.desc())
            .limit(20)
            .all()
        )
        tenant_cases.extend(_sanitized_memory_row(case_type, row) for row in rows)
    mode_token = _normalize_mode(mode or signature_payload.get("mode"))
    risk_flags = signature_payload.get("risk_flags") if isinstance(signature_payload.get("risk_flags"), list) else []
    scored = []
    for item in tenant_cases:
        score = _score_memory_candidate(
            candidate=item,
            similarity_index_key=similarity_index_key,
            normalized_problem_signature=normalized_signature,
            mode=mode_token,
            risk_flags=risk_flags,
        )
        if score <= 0:
            continue
        scored.append({**item, "score": score})
    scored.sort(key=lambda item: (float(item.get("score") or 0.0), item.get("created_at") or ""), reverse=True)
    top_similar = scored[:3]

    failed_items = [item for item in scored if item.get("case_type") == "failed"]
    last_failed = failed_items[0] if failed_items else None

    solved_items = [item for item in scored if item.get("case_type") in {"solved", "recovered"}]
    solved_items.sort(
        key=lambda item: (
            float(item.get("score") or 0.0),
            -int(_safe_dict(item.get("outcome")).get("duration_ms") or 0),
        ),
        reverse=True,
    )
    best_solved = solved_items[0] if solved_items else None

    signals = [_serialize_signal(item) for item in _active_signal_rows(db, tenant_id=int(file_row.tenant_id), similarity_index_key=similarity_index_key)]
    return {
        "normalized_problem_signature": normalized_signature,
        "similarity_index_key": similarity_index_key,
        "signature_context": signature_payload,
        "top_similar_cases": top_similar,
        "last_failed_case": last_failed,
        "best_solved_pattern": best_solved,
        "active_signals": signals,
    }


def store_experience_entry(
    db: Session,
    *,
    task_query: str,
    successful_plan: dict[str, Any],
    lessons_learned: str | None,
    feedback_from_owner: str | None,
) -> dict[str, Any]:
    identifier = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO experience_ledger (
              id,
              task_query,
              successful_plan,
              lessons_learned,
              feedback_from_owner,
              created_at
            )
            VALUES (
              :id,
              :task_query,
              CAST(:successful_plan AS JSONB),
              :lessons_learned,
              :feedback_from_owner,
              NOW()
            )
            """
        ),
        {
            "id": identifier,
            "task_query": task_query,
            "successful_plan": json.dumps(_safe_dict(successful_plan), ensure_ascii=True),
            "lessons_learned": lessons_learned,
            "feedback_from_owner": feedback_from_owner,
        },
    )
    db.commit()
    return {"id": identifier, "status": "stored", "stored_at": _now().isoformat()}


def search_experience_entries(db: Session, *, query: str, limit: int) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT
              id,
              task_query,
              successful_plan,
              lessons_learned,
              feedback_from_owner,
              created_at
            FROM experience_ledger
            WHERE task_query ILIKE :query
               OR COALESCE(lessons_learned, '') ILIKE :query
               OR COALESCE(feedback_from_owner, '') ILIKE :query
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"query": f"%{query.strip()}%", "limit": limit},
    ).mappings()
    items = [
        {
            "id": str(row["id"]),
            "task_query": row["task_query"],
            "successful_plan": row["successful_plan"] if isinstance(row["successful_plan"], dict) else {},
            "lessons_learned": row["lessons_learned"],
            "feedback_from_owner": row["feedback_from_owner"],
            "created_at": row["created_at"].isoformat() if row["created_at"] is not None else None,
        }
        for row in rows
    ]
    return {"query": query, "items": items, "total": len(items)}


def store_decision_log(
    db: Session,
    *,
    prompt: str,
    lane: str,
    executor: str,
    decision_json: dict[str, Any],
) -> dict[str, Any]:
    decision_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO decision_logs (
              decision_id,
              prompt,
              lane,
              executor,
              decision_json,
              created_at
            )
            VALUES (
              :decision_id,
              :prompt,
              :lane,
              :executor,
              CAST(:decision_json AS JSONB),
              NOW()
            )
            """
        ),
        {
            "decision_id": decision_id,
            "prompt": prompt,
            "lane": lane,
            "executor": executor,
            "decision_json": json.dumps(_safe_dict(decision_json), ensure_ascii=True),
        },
    )
    db.commit()
    return {"decision_id": decision_id, "logged_at": _now().isoformat()}
