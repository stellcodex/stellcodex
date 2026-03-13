"""Persistence helpers for deterministic engineering artifacts.

This layer is responsible for turning runtime outputs into stable, schema-backed
records. Keep fallback builders aligned with the runtime contract so persisted
artifacts and in-memory artifacts stay equivalent.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.engineering import (
    build_cost_estimate,
    build_engineering_dfm_report,
    build_engineering_report,
    build_feature_map,
    build_manufacturing_decision,
    build_manufacturing_plan,
    build_runtime_geometry_metrics,
)
from app.models.engineering import (
    AnalysisRun,
    ArtifactCacheEntry,
    CostEstimateRecord,
    CostOptimizationRecord,
    DesignIntentRecord,
    DesignOptimizationRecord,
    DfmReportRecord,
    EngineeringReportRecord,
    FeatureMap,
    GeometryMetric,
    ManufacturingPlanRecord,
    ProcessSimulationRecord,
)
from app.models.file import UploadFile


def _stable_hash(payload: dict[str, Any] | None) -> str:
    encoded = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def build_geometry_hash(
    *,
    mode: str,
    source_ext: str,
    geometry_meta: dict[str, Any] | None = None,
    geometry_report: dict[str, Any] | None = None,
    bounding_box: dict[str, Any] | None = None,
    feature_flags: dict[str, Any] | None = None,
    part_count: int | None = None,
    triangle_count: int | None = None,
) -> str:
    payload = {
        "mode": str(mode or "visual_only"),
        "source_ext": str(source_ext or "").lower(),
        "geometry_meta": _as_dict(geometry_meta),
        "geometry_report": _as_dict(geometry_report),
        "bounding_box": _as_dict(bounding_box),
        "feature_flags": _as_dict(feature_flags),
        "part_count": _as_int(part_count),
        "triangle_count": _as_int(triangle_count),
    }
    return _stable_hash(payload)


def geometry_hash_for_upload(row: UploadFile, analysis_result: dict[str, Any] | None = None) -> str:
    meta = _as_dict(getattr(row, "meta", {}))
    result = _as_dict(analysis_result)
    geometry_meta = _as_dict(meta.get("geometry_meta_json"))
    geometry_report = _as_dict(meta.get("geometry_report"))
    feature_flags = _as_dict(result.get("feature_flags"))
    bounding_box = _as_dict(result.get("bounding_box") or geometry_meta.get("bbox"))
    part_count = (
        _as_int(result.get("part_count"))
        or _as_int(feature_flags.get("part_count"))
        or _as_int(meta.get("part_count"))
        or _as_int(geometry_meta.get("part_count"))
    )
    triangle_count = (
        _as_int(result.get("triangle_count"))
        or _as_int(feature_flags.get("triangle_count"))
        or _as_int(feature_flags.get("face_count"))
        or _as_int(geometry_meta.get("triangle_count"))
    )
    mode = str(result.get("mode") or meta.get("mode") or "visual_only")
    source_ext = Path(str(getattr(row, "original_filename", "") or "")).suffix.lower().lstrip(".")
    return build_geometry_hash(
        mode=mode,
        source_ext=source_ext,
        geometry_meta=geometry_meta,
        geometry_report=geometry_report,
        bounding_box=bounding_box,
        feature_flags=feature_flags,
        part_count=part_count,
        triangle_count=triangle_count,
    )


def start_analysis_run(
    db: Session,
    *,
    row: UploadFile,
    run_type: str,
    session_id: str | None = None,
    metrics: dict[str, Any] | None = None,
) -> AnalysisRun:
    run = AnalysisRun(
        tenant_id=int(row.tenant_id),
        file_id=str(row.file_id),
        session_id=str(session_id or ""),
        run_type=str(run_type or "engineering_analysis"),
        status="running",
        started_at=datetime.utcnow(),
        metrics_json=_as_dict(metrics),
    )
    db.add(run)
    return run


def finalize_analysis_run(
    db: Session,
    run: AnalysisRun,
    *,
    result: dict[str, Any],
    geometry_hash: str | None,
    error_code: str | None = None,
) -> AnalysisRun:
    payload = dict(_as_dict(run.metrics_json))
    payload.update(
        {
            "mode": result.get("mode"),
            "capability_status": result.get("capability_status"),
            "geometry_hash": geometry_hash,
            "unavailable_reason": result.get("unavailable_reason"),
        }
    )
    run.ended_at = datetime.utcnow()
    run.metrics_json = payload
    run.error_code = str(error_code or result.get("unavailable_reason") or "") or None
    run.status = "degraded" if run.error_code else "completed"
    db.add(run)
    return run


def _build_geometry_metrics(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("geometry_metrics"))
    if payload:
        return payload

    flags = _as_dict(result.get("feature_flags"))
    return build_runtime_geometry_metrics(
        file_id=str(result.get("file_id") or ""),
        mode=str(result.get("mode") or "visual_only"),
        units=str(result.get("units") or "mm"),
        bbox=_as_dict(result.get("bounding_box")),
        volume=_as_float(result.get("volume")),
        surface_area=_as_float(result.get("surface_area")),
        part_count=_as_int(result.get("part_count")) or _as_int(flags.get("part_count")),
        triangle_count=_as_int(result.get("triangle_count")) or _as_int(flags.get("triangle_count")) or _as_int(flags.get("face_count")),
        source_type=str(result.get("source_type") or "engineering_analysis"),
        confidence=float(result.get("confidence") or 0.0),
        feature_flags=flags,
        wall_thickness_stats=_as_dict(result.get("wall_thickness_stats")),
        metadata={
            "capability_status": result.get("capability_status"),
            "unavailable_reason": result.get("unavailable_reason"),
        },
    )


def _build_feature_map(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("feature_map"))
    if payload:
        return payload

    geometry_metrics = _build_geometry_metrics(result)
    return build_feature_map(
        mode=str(result.get("mode") or "visual_only"),
        geometry_metrics=geometry_metrics,
        feature_flags=_as_dict(result.get("feature_flags")),
        source_signals=_as_dict(result.get("source_signals")),
    )


def _build_manufacturing_decision(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("manufacturing_decision"))
    if payload:
        return payload
    geometry_metrics = _build_geometry_metrics(result)
    feature_map = _build_feature_map(result)
    return build_manufacturing_decision(
        mode=str(result.get("mode") or "visual_only"),
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )


def _build_manufacturing_plan(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("manufacturing_plan"))
    if payload:
        return payload
    return build_manufacturing_plan(
        geometry_metrics=_build_geometry_metrics(result),
        feature_map=_build_feature_map(result),
        manufacturing_decision=_build_manufacturing_decision(result),
    )


def _build_design_intent(result: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(result.get("design_intent"))


def _build_process_simulation(result: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(result.get("process_simulation"))


def _build_cost_optimization(result: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(result.get("cost_optimization"))


def _build_design_optimization(result: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(result.get("design_optimization"))


def _build_cost_estimate(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("cost_estimate"))
    if payload:
        return payload
    return build_cost_estimate(
        geometry_metrics=_build_geometry_metrics(result),
        feature_map=_build_feature_map(result),
        manufacturing_decision=_build_manufacturing_decision(result),
        manufacturing_plan=_build_manufacturing_plan(result),
    )


def _build_dfm_report(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("dfm_report"))
    if payload:
        return payload
    manufacturing_decision = _build_manufacturing_decision(result)
    return build_engineering_dfm_report(
        file_id=str(result.get("file_id") or ""),
        session_id=str(result.get("session_id") or "") or None,
        mode=str(result.get("mode") or "visual_only"),
        confidence=float(result.get("confidence") or 0.0),
        rule_version=str(result.get("rule_version") or "engineering_dfm.v1"),
        rule_explanations=result.get("rule_explanations") if isinstance(result.get("rule_explanations"), list) else [],
        geometry_metrics=_build_geometry_metrics(result),
        feature_map=_build_feature_map(result),
        manufacturing_decision=manufacturing_decision or {"recommended_process": result.get("recommended_process")},
        risk_analysis=result.get("dfm_risk") if isinstance(result.get("dfm_risk"), list) else [],
        recommendations=result.get("recommendations") if isinstance(result.get("recommendations"), list) else [],
        capability_status=manufacturing_decision.get("capability_status") or result.get("capability_status"),
        unavailable_reason=result.get("unavailable_reason"),
    )


def _build_engineering_report(result: dict[str, Any]) -> dict[str, Any]:
    payload = _as_dict(result.get("engineering_report"))
    if payload:
        return payload
    return build_engineering_report(
        file_id=str(result.get("file_id") or ""),
        geometry_metrics=_build_geometry_metrics(result),
        feature_map=_build_feature_map(result),
        manufacturing_decision=_build_manufacturing_decision(result),
        manufacturing_plan=_build_manufacturing_plan(result),
        cost_estimate=_build_cost_estimate(result),
        dfm_report=_build_dfm_report(result),
    )


def _upsert_geometry_metrics(
    db: Session,
    *,
    row: UploadFile,
    result: dict[str, Any],
    geometry_hash: str,
) -> GeometryMetric:
    record = (
        db.query(GeometryMetric)
        .filter(
            GeometryMetric.tenant_id == int(row.tenant_id),
            GeometryMetric.file_id == str(row.file_id),
            GeometryMetric.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = GeometryMetric(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    payload = _build_geometry_metrics(result)
    flags = _as_dict(result.get("feature_flags"))
    bbox = _as_dict(payload.get("bbox") or result.get("bounding_box") or _as_dict((row.meta or {}).get("geometry_meta_json")).get("bbox"))
    metadata_json = _as_dict(payload.get("metadata"))
    metadata_json.update(
        {
            "capability_status": result.get("capability_status"),
            "unavailable_reason": result.get("unavailable_reason"),
            "source_type": payload.get("source_type"),
            "confidence": payload.get("confidence"),
        }
    )
    record.mode = str(payload.get("mode") or result.get("mode") or (row.meta or {}).get("mode") or "visual_only")
    record.units = str(payload.get("units") or result.get("units") or "mm")
    record.volume = _as_float(payload.get("volume"))
    record.surface_area = _as_float(payload.get("surface_area"))
    record.bbox_json = bbox
    record.triangle_count = _as_int(payload.get("triangle_count")) or _as_int(flags.get("triangle_count")) or _as_int(flags.get("face_count"))
    record.part_count = _as_int(payload.get("part_count")) or _as_int(flags.get("part_count")) or _as_int((row.meta or {}).get("part_count"))
    record.wall_thickness_stats = _as_dict(payload.get("wall_thickness_stats"))
    record.mass_estimate = _as_float(payload.get("mass_estimate"))
    record.metadata_json = {
        **metadata_json,
    }
    db.add(record)
    return record


def _upsert_feature_map(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
) -> FeatureMap:
    record = (
        db.query(FeatureMap)
        .filter(
            FeatureMap.tenant_id == int(row.tenant_id),
            FeatureMap.file_id == str(row.file_id),
            FeatureMap.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = FeatureMap(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    record.feature_map_json = _build_feature_map(result)
    record.extractor_version = str(record.feature_map_json.get("extractor_version") or "engineering_features.v2")
    db.add(record)
    return record


def _upsert_dfm_report(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> DfmReportRecord:
    rule_version = str(result.get("rule_version") or "engineering_dfm.v1")
    manufacturing_decision = _build_manufacturing_decision(result)
    report_payload = _build_dfm_report(result)
    record = (
        db.query(DfmReportRecord)
        .filter(
            DfmReportRecord.tenant_id == int(row.tenant_id),
            DfmReportRecord.file_id == str(row.file_id),
            DfmReportRecord.geometry_hash == str(geometry_hash),
            DfmReportRecord.rule_version == rule_version,
        )
        .first()
    )
    if record is None:
        record = DfmReportRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
            rule_version=rule_version,
        )
    report_json = report_payload
    record.session_id = str(session_id or "") or None
    record.mode = str(report_json["mode"])
    record.confidence = float(report_json["confidence"])
    record.report_json = report_json
    record.report_hash = _stable_hash(report_json)
    db.add(record)
    return record


def _upsert_design_intent(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> DesignIntentRecord | None:
    payload = _build_design_intent(result)
    if not payload:
        return None
    record = (
        db.query(DesignIntentRecord)
        .filter(
            DesignIntentRecord.tenant_id == int(row.tenant_id),
            DesignIntentRecord.file_id == str(row.file_id),
            DesignIntentRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = DesignIntentRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    record.session_id = str(session_id or "") or None
    record.intent_json = payload
    record.intent_hash = _stable_hash(payload)
    db.add(record)
    return record


def _upsert_cost_estimate(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> CostEstimateRecord:
    record = (
        db.query(CostEstimateRecord)
        .filter(
            CostEstimateRecord.tenant_id == int(row.tenant_id),
            CostEstimateRecord.file_id == str(row.file_id),
            CostEstimateRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = CostEstimateRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    estimate = _build_cost_estimate(result)
    record.session_id = str(session_id or "") or None
    record.recommended_process = str(estimate.get("recommended_process") or "unknown")
    record.currency = str(estimate.get("currency") or "EUR")
    record.estimated_unit_cost = _as_float(estimate.get("estimated_unit_cost"))
    record.estimated_batch_cost = _as_float(estimate.get("estimated_batch_cost"))
    record.estimate_json = estimate
    record.estimate_hash = _stable_hash(estimate)
    db.add(record)
    return record


def _upsert_cost_optimization(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> CostOptimizationRecord | None:
    payload = _build_cost_optimization(result)
    if not payload:
        return None
    record = (
        db.query(CostOptimizationRecord)
        .filter(
            CostOptimizationRecord.tenant_id == int(row.tenant_id),
            CostOptimizationRecord.file_id == str(row.file_id),
            CostOptimizationRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = CostOptimizationRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    record.session_id = str(session_id or "") or None
    record.optimization_json = payload
    record.optimization_hash = _stable_hash(payload)
    db.add(record)
    return record


def _upsert_manufacturing_plan(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> ManufacturingPlanRecord:
    record = (
        db.query(ManufacturingPlanRecord)
        .filter(
            ManufacturingPlanRecord.tenant_id == int(row.tenant_id),
            ManufacturingPlanRecord.file_id == str(row.file_id),
            ManufacturingPlanRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = ManufacturingPlanRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    plan = _build_manufacturing_plan(result)
    record.session_id = str(session_id or "") or None
    record.recommended_process = str(plan.get("recommended_process") or "unknown")
    record.setup_count = _as_int(plan.get("setup_count"))
    record.estimated_cycle_time_minutes = _as_float(plan.get("estimated_cycle_time_minutes"))
    record.estimated_batch_time_minutes = _as_float(plan.get("estimated_batch_time_minutes"))
    record.plan_json = plan
    record.plan_hash = _stable_hash(plan)
    db.add(record)
    return record


def _upsert_process_simulation(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> ProcessSimulationRecord | None:
    payload = _build_process_simulation(result)
    if not payload:
        return None
    record = (
        db.query(ProcessSimulationRecord)
        .filter(
            ProcessSimulationRecord.tenant_id == int(row.tenant_id),
            ProcessSimulationRecord.file_id == str(row.file_id),
            ProcessSimulationRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = ProcessSimulationRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    record.session_id = str(session_id or "") or None
    record.simulation_json = payload
    record.simulation_hash = _stable_hash(payload)
    db.add(record)
    return record


def _upsert_engineering_report(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> EngineeringReportRecord:
    record = (
        db.query(EngineeringReportRecord)
        .filter(
            EngineeringReportRecord.tenant_id == int(row.tenant_id),
            EngineeringReportRecord.file_id == str(row.file_id),
            EngineeringReportRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = EngineeringReportRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    report = _build_engineering_report(result)
    record.session_id = str(session_id or "") or None
    record.capability_status = str(report.get("capability_status") or "degraded")
    record.report_json = report
    record.report_hash = str(report.get("report_hash") or _stable_hash(report))
    db.add(record)
    return record


def _upsert_design_optimization(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    result: dict[str, Any],
    session_id: str | None,
) -> DesignOptimizationRecord | None:
    payload = _build_design_optimization(result)
    if not payload:
        return None
    record = (
        db.query(DesignOptimizationRecord)
        .filter(
            DesignOptimizationRecord.tenant_id == int(row.tenant_id),
            DesignOptimizationRecord.file_id == str(row.file_id),
            DesignOptimizationRecord.geometry_hash == str(geometry_hash),
        )
        .first()
    )
    if record is None:
        record = DesignOptimizationRecord(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
        )
    record.session_id = str(session_id or "") or None
    record.optimization_json = payload
    record.optimization_hash = _stable_hash(payload)
    db.add(record)
    return record


def _upsert_artifact_cache(
    db: Session,
    *,
    row: UploadFile,
    geometry_hash: str,
    analysis_type: str,
    payload: dict[str, Any],
) -> ArtifactCacheEntry:
    record = (
        db.query(ArtifactCacheEntry)
        .filter(
            ArtifactCacheEntry.tenant_id == int(row.tenant_id),
            ArtifactCacheEntry.file_id == str(row.file_id),
            ArtifactCacheEntry.geometry_hash == str(geometry_hash),
            ArtifactCacheEntry.analysis_type == str(analysis_type),
        )
        .first()
    )
    if record is None:
        record = ArtifactCacheEntry(
            tenant_id=int(row.tenant_id),
            file_id=str(row.file_id),
            geometry_hash=str(geometry_hash),
            analysis_type=str(analysis_type),
        )
    record.artifact_hash = _stable_hash(payload)
    record.artifact_uri_ref = f"scx://files/{row.file_id}/{analysis_type}"
    record.metadata_json = {
        "mode": payload.get("mode") or payload.get("recommended_process"),
        "capability_status": payload.get("capability_status"),
        "unavailable_reason": payload.get("unavailable_reason"),
    }
    db.add(record)
    return record


def _artifact_payloads(result: dict[str, Any], analysis_type: str) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {
        analysis_type: _as_dict(result),
    }
    for artifact_type in (
        "design_intent",
        "process_simulation",
        "cost_optimization",
        "design_optimization",
        "engineering_decision",
        "engineering_master_report",
    ):
        payload = _as_dict(result.get(artifact_type))
        if payload:
            payloads[artifact_type] = payload
    return payloads


def persist_engineering_analysis(
    db: Session,
    *,
    row: UploadFile,
    result: dict[str, Any],
    analysis_type: str = "engineering_analysis",
    session_id: str | None = None,
) -> str:
    geometry_hash = geometry_hash_for_upload(row, analysis_result=result)
    _upsert_geometry_metrics(db, row=row, result=result, geometry_hash=geometry_hash)
    _upsert_feature_map(db, row=row, geometry_hash=geometry_hash, result=result)
    _upsert_design_intent(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_dfm_report(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_cost_estimate(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_cost_optimization(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_manufacturing_plan(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_process_simulation(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_engineering_report(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    _upsert_design_optimization(db, row=row, geometry_hash=geometry_hash, result=result, session_id=session_id)
    for artifact_type, payload in _artifact_payloads(result, analysis_type).items():
        _upsert_artifact_cache(
            db,
            row=row,
            geometry_hash=geometry_hash,
            analysis_type=artifact_type,
            payload=payload,
        )
    return geometry_hash
