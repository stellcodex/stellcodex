"""Guarded engineering runtime entry point.

This module materializes uploaded geometry, applies capability gating, and
returns the deterministic engineering artifact chain used by STELL-AI tools,
workers, and persistence.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy.orm import Session

from app.core.engineering import (
    MODE_VISUAL_ONLY,
    build_cost_estimate,
    build_engineering_dfm_report,
    build_engineering_report,
    build_feature_map,
    build_manufacturing_decision,
    build_manufacturing_plan,
    build_runtime_geometry_metrics,
)
from app.core.format_registry import infer_mime_from_bytes
from app.core.storage import get_s3_client
from app.models.file import UploadFile
from app.storage import Storage
from app.stellai.engineering.policy import detect_engineering_capability, occ_available

try:
    import trimesh
except Exception:  # pragma: no cover - optional runtime dependency
    trimesh = None


MAX_ANALYSIS_FILE_BYTES = int(os.getenv("STELLAI_ENGINEERING_MAX_FILE_BYTES", str(80 * 1024 * 1024)) or 80 * 1024 * 1024)
MAX_ANALYSIS_VERTICES = int(os.getenv("STELLAI_ENGINEERING_MAX_VERTICES", "2000000") or "2000000")
MAX_ANALYSIS_FACES = int(os.getenv("STELLAI_ENGINEERING_MAX_FACES", "2000000") or "2000000")
MAX_ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("STELLAI_ENGINEERING_TIMEOUT_SECONDS", "45") or "45")
MAX_ANALYSIS_MEMORY_BYTES = int(os.getenv("STELLAI_ENGINEERING_MAX_MEMORY_BYTES", str(512 * 1024 * 1024)) or 512 * 1024 * 1024)
MAX_ANALYSIS_CONCURRENCY = max(1, int(os.getenv("STELLAI_ENGINEERING_MAX_CONCURRENCY", "1") or "1"))
ALLOWED_ENGINEERING_EXTS = {"step", "stp", "stl", "obj", "ply", "gltf", "glb", "dxf", "iges", "igs", "x_t", "x_b"}

_ANALYSIS_SEMAPHORE = threading.BoundedSemaphore(MAX_ANALYSIS_CONCURRENCY)


class EngineeringAnalysisError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = str(code or "engineering_error")
        self.message = str(message or "Engineering analysis failed")
        super().__init__(self.message)


def load_upload_for_tenant(db: Session | None, *, file_id: str, tenant_id: str) -> UploadFile:
    if db is None:
        raise EngineeringAnalysisError("db_unavailable", "Database session is required")
    row = db.query(UploadFile).filter(UploadFile.file_id == str(file_id)).first()
    if row is None:
        raise EngineeringAnalysisError("file_not_found", "Referenced file was not found")
    if str(row.tenant_id) != str(tenant_id):
        raise EngineeringAnalysisError("tenant_mismatch", "Referenced file does not belong to the active tenant")
    return row


def resolve_file_id(file_id: str | None, fallback_ids: tuple[str, ...]) -> str:
    explicit = str(file_id or "").strip()
    if explicit:
        return explicit
    if fallback_ids:
        return str(fallback_ids[0])
    raise EngineeringAnalysisError("missing_file_id", "Engineering analysis requires a file_id")


@contextmanager
def materialize_upload(row: UploadFile) -> Iterator[Path]:
    from app.core.config import settings

    if settings.s3_enabled:
        tmp_dir = Path(tempfile.mkdtemp(prefix="stell_eng_"))
        tmp_path = tmp_dir / _safe_filename(row.original_filename)
        try:
            s3 = get_s3_client(settings)
            obj = s3.get_object(Bucket=row.bucket, Key=row.object_key)
            tmp_path.write_bytes(obj["Body"].read())
            yield tmp_path
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    local_path = Storage().root / str(row.object_key)
    if not local_path.exists():
        raise EngineeringAnalysisError("file_not_found", "File payload is not available in runtime storage")
    yield local_path


def analyze_upload(row: UploadFile) -> dict[str, Any]:
    with materialize_upload(row) as local_path:
        return analyze_file(
            file_id=str(row.file_id),
            filename=str(row.original_filename),
            size_bytes=int(row.size_bytes),
            local_path=local_path,
        )


def analyze_file(*, file_id: str, filename: str, size_bytes: int, local_path: Path) -> dict[str, Any]:
    capability = detect_engineering_capability(filename, occ_enabled=occ_available())
    _validate_security(local_path=local_path, filename=filename, size_bytes=size_bytes)

    if capability["capability_status"] in {"unsupported", "preview_only", "experimental"}:
        return _base_unavailable(file_id=file_id, capability=capability)

    if not _ANALYSIS_SEMAPHORE.acquire(blocking=False):
        return _base_unavailable(
            file_id=file_id,
            capability={**capability, "capability_status": "busy"},
            unavailable_reason="Engineering analysis queue is busy",
        )

    started_at = time.monotonic()
    try:
        estimated_memory = max(size_bytes * 8, size_bytes)
        if estimated_memory > MAX_ANALYSIS_MEMORY_BYTES:
            raise EngineeringAnalysisError("memory_ceiling_exceeded", "Estimated memory usage exceeds configured ceiling")

        if capability["mode"] == "mesh_approx":
            result = _analyze_mesh(file_id=file_id, local_path=local_path, capability=capability)
        elif capability["mode"] == "brep":
            result = _analyze_step(file_id=file_id, local_path=local_path, capability=capability)
        else:
            result = _base_unavailable(file_id=file_id, capability=capability)

        if (time.monotonic() - started_at) > MAX_ANALYSIS_TIMEOUT_SECONDS:
            raise EngineeringAnalysisError("analysis_timeout", "Engineering analysis exceeded timeout limit")
        return result
    except EngineeringAnalysisError as exc:
        return _base_unavailable(
            file_id=file_id,
            capability=capability,
            unavailable_reason=exc.code,
        )
    finally:
        _ANALYSIS_SEMAPHORE.release()


def analysis_limits() -> dict[str, Any]:
    return {
        "max_file_size_bytes": MAX_ANALYSIS_FILE_BYTES,
        "max_vertex_count": MAX_ANALYSIS_VERTICES,
        "max_face_count": MAX_ANALYSIS_FACES,
        "timeout_seconds": MAX_ANALYSIS_TIMEOUT_SECONDS,
        "memory_ceiling_bytes": MAX_ANALYSIS_MEMORY_BYTES,
        "max_concurrency": MAX_ANALYSIS_CONCURRENCY,
    }


def _validate_security(*, local_path: Path, filename: str, size_bytes: int) -> None:
    ext = Path(filename or "").suffix.lower().lstrip(".")
    if ext not in ALLOWED_ENGINEERING_EXTS:
        raise EngineeringAnalysisError("unsupported_format", "File extension is not allowed for engineering analysis")
    if size_bytes > MAX_ANALYSIS_FILE_BYTES:
        raise EngineeringAnalysisError("file_too_large", "File exceeds engineering analysis file-size limit")
    if not local_path.exists() or not local_path.is_file():
        raise EngineeringAnalysisError("file_not_found", "Local analysis payload is unavailable")
    head = local_path.read_bytes()[:8192]
    sniffed = infer_mime_from_bytes(head, filename)
    if sniffed == "application/zip":
        raise EngineeringAnalysisError("archive_rejected", "Archive payloads are not accepted for engineering analysis")


def _analyze_mesh(*, file_id: str, local_path: Path, capability: dict[str, Any]) -> dict[str, Any]:
    if trimesh is None:
        return _base_unavailable(
            file_id=file_id,
            capability={**capability, "capability_status": "dependency_missing"},
            unavailable_reason="mesh_stack_unavailable",
        )

    try:
        loaded = trimesh.load(local_path, force="mesh", process=False, skip_materials=True)
        part_count: int | None = None
        if isinstance(loaded, trimesh.Scene):
            geometries = [geom for geom in loaded.geometry.values() if isinstance(geom, trimesh.Trimesh)]
            if not geometries:
                raise EngineeringAnalysisError("empty_scene", "No mesh geometry was found")
            mesh = trimesh.util.concatenate(geometries)
            if len(geometries) == 1:
                part_count = 1
        elif isinstance(loaded, trimesh.Trimesh):
            mesh = loaded
            part_count = 1
        else:
            raise EngineeringAnalysisError("mesh_unavailable", "Mesh payload could not be loaded")
    except EngineeringAnalysisError:
        raise
    except Exception as exc:  # pragma: no cover - parser/library dependent
        raise EngineeringAnalysisError("geometry_rejected", exc.__class__.__name__) from exc

    vertex_count = int(len(mesh.vertices))
    face_count = int(len(mesh.faces))
    if vertex_count > MAX_ANALYSIS_VERTICES:
        raise EngineeringAnalysisError("vertex_limit_exceeded", "Vertex count exceeds configured limit")
    if face_count > MAX_ANALYSIS_FACES:
        raise EngineeringAnalysisError("face_limit_exceeded", "Face count exceeds configured limit")

    bounds = mesh.bounds.tolist() if getattr(mesh, "bounds", None) is not None else [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    extents = mesh.extents.tolist() if getattr(mesh, "extents", None) is not None else [0.0, 0.0, 0.0]
    bbox = {
        "min": [round(float(item), 6) for item in bounds[0]],
        "max": [round(float(item), 6) for item in bounds[1]],
        "size": [round(float(item), 6) for item in extents],
    }
    feature_flags = {
        "vertex_count": vertex_count,
        "face_count": face_count,
        "is_watertight": bool(mesh.is_watertight),
        "is_volume": bool(mesh.is_volume),
        "component_count": int(len(mesh.split(only_watertight=False))),
    }
    risks: list[dict[str, Any]] = []
    recommendations: list[str] = []
    explanations: list[str] = []
    thin_ratio = _thin_ratio(extents)
    if not feature_flags["is_watertight"]:
        risks.append({"code": "mesh_not_watertight", "severity": "medium"})
        recommendations.append("Close open boundaries before manufacturing review.")
        explanations.append("DFM confidence is reduced because the mesh is not watertight.")
    if thin_ratio < 0.08:
        risks.append({"code": "thin_section_proxy", "severity": "medium"})
        recommendations.append("Review thin sections against process minimum wall guidance.")
        explanations.append("Bounding-box ratios indicate a possible thin-section condition.")

    confidence = 0.78 if feature_flags["is_watertight"] else 0.56
    geometry_metrics = build_runtime_geometry_metrics(
        file_id=file_id,
        mode=capability["mode"],
        source_type="mesh_runtime",
        confidence=confidence,
        bbox=bbox,
        volume=float(mesh.volume) if feature_flags["is_volume"] else None,
        surface_area=float(mesh.area),
        part_count=part_count,
        triangle_count=face_count,
        feature_flags=feature_flags,
        metadata={"capability_status": capability["capability_status"]},
    )
    feature_map = build_feature_map(
        mode=geometry_metrics["mode"],
        geometry_metrics=geometry_metrics,
        feature_flags=feature_flags,
        source_signals={"is_watertight": feature_flags["is_watertight"]},
    )
    (
        manufacturing_decision,
        manufacturing_plan,
        cost_estimate,
    ) = _build_engineering_outputs(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )
    dfm_report = build_engineering_dfm_report(
        file_id=file_id,
        mode=capability["mode"],
        confidence=confidence,
        rule_version="engineering_dfm.v1",
        rule_explanations=explanations,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        risk_analysis=risks,
        recommendations=recommendations,
        capability_status=capability["capability_status"],
        unavailable_reason=None,
    )
    engineering_report = build_engineering_report(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=manufacturing_plan,
        cost_estimate=cost_estimate,
        dfm_report=dfm_report,
    )
    return {
        "file_id": file_id,
        "mode": capability["mode"],
        "confidence": round(confidence, 4),
        "capability_status": capability["capability_status"],
        "units": "mm",
        "volume": geometry_metrics.get("volume"),
        "surface_area": geometry_metrics.get("surface_area"),
        "bounding_box": geometry_metrics.get("bbox"),
        "part_count": geometry_metrics.get("part_count"),
        "triangle_count": geometry_metrics.get("triangle_count"),
        "wall_thickness_stats": geometry_metrics.get("wall_thickness_stats"),
        "feature_flags": feature_flags,
        "geometry_metrics": geometry_metrics,
        "feature_map": feature_map,
        "manufacturing_decision": manufacturing_decision,
        "manufacturing_plan": manufacturing_plan,
        "cost_estimate": cost_estimate,
        "dfm_report": dfm_report,
        "engineering_report": engineering_report,
        "recommended_process": manufacturing_decision.get("recommended_process"),
        "estimated_unit_cost": cost_estimate.get("estimated_unit_cost"),
        "estimated_batch_cost": cost_estimate.get("estimated_batch_cost"),
        "dfm_risk": risks,
        "recommendations": recommendations + list(manufacturing_decision.get("recommended_changes") or []),
        "rule_version": "engineering_dfm.v1",
        "rule_explanations": explanations,
        "unavailable_reason": None,
    }


def _analyze_step(*, file_id: str, local_path: Path, capability: dict[str, Any]) -> dict[str, Any]:
    from app.services.step_extractor import extract_step_geometry

    result = extract_step_geometry(local_path)
    bbox = result.bbox
    feature_flags = {
        "solid_count": int(result.solid_count),
        "part_count": int(result.part_count),
        "hole_count": int(len(result.holes)),
        "thread_hints": bool(result.thread_hints),
        "surface_breakdown": result.surfaces.to_dict() if hasattr(result.surfaces, "to_dict") else {
            "plane": int(result.surfaces.plane),
            "cylindrical": int(result.surfaces.cylindrical),
            "conical": int(result.surfaces.conical),
            "spherical": int(result.surfaces.spherical),
            "toroidal": int(result.surfaces.toroidal),
            "b_spline": int(result.surfaces.b_spline),
            "other": int(result.surfaces.other),
        },
    }
    risks: list[dict[str, Any]] = []
    recommendations: list[str] = []
    explanations: list[str] = []
    if capability["capability_status"] != "brep_ready":
        risks.append({"code": "occ_path_unavailable", "severity": "medium"})
        recommendations.append("Enable the OCC path for full B-Rep interrogation.")
        explanations.append("STEP analysis is limited to deterministic text extraction because OCC is unavailable.")
    if bbox is not None and min(bbox.x, bbox.y, bbox.z) <= 0:
        risks.append({"code": "invalid_bbox", "severity": "high"})
        recommendations.append("Validate source geometry before release.")
        explanations.append("Extracted STEP bounding box is incomplete or invalid.")

    bbox_payload = (
        {
            "min": None,
            "max": None,
            "size": [round(float(bbox.x), 6), round(float(bbox.y), 6), round(float(bbox.z), 6)],
        }
        if bbox is not None
        else None
    )
    geometry_metrics = build_runtime_geometry_metrics(
        file_id=file_id,
        mode="brep",
        source_type="step_runtime",
        confidence=float(capability["confidence"]),
        bbox=bbox_payload,
        volume=float(result.volume_mm3) if result.volume_mm3 is not None else None,
        surface_area=None,
        part_count=int(result.part_count),
        triangle_count=None,
        feature_flags=feature_flags,
        metadata={
            "capability_status": capability["capability_status"],
            "solid_count": int(result.solid_count),
            "complexity": result.complexity.label,
        },
    )
    feature_map = build_feature_map(
        mode=geometry_metrics["mode"],
        geometry_metrics=geometry_metrics,
        feature_flags=feature_flags,
        source_signals={
            "thread_hints": result.thread_hints,
            "surface_breakdown": feature_flags["surface_breakdown"],
            "hole_details": [hole.to_dict() if hasattr(hole, "to_dict") else {} for hole in result.holes],
        },
    )
    (
        manufacturing_decision,
        manufacturing_plan,
        cost_estimate,
    ) = _build_engineering_outputs(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )
    dfm_report = build_engineering_dfm_report(
        file_id=file_id,
        mode="brep",
        confidence=float(capability["confidence"]),
        rule_version="engineering_dfm.v1",
        rule_explanations=explanations,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        risk_analysis=risks,
        recommendations=recommendations,
        capability_status=capability["capability_status"],
        unavailable_reason=capability.get("unavailable_reason"),
    )
    engineering_report = build_engineering_report(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=manufacturing_plan,
        cost_estimate=cost_estimate,
        dfm_report=dfm_report,
    )
    return {
        "file_id": file_id,
        "mode": "brep",
        "confidence": round(float(capability["confidence"]), 4),
        "capability_status": capability["capability_status"],
        "units": "mm",
        "volume": geometry_metrics.get("volume"),
        "surface_area": geometry_metrics.get("surface_area"),
        "bounding_box": geometry_metrics.get("bbox"),
        "part_count": geometry_metrics.get("part_count"),
        "triangle_count": geometry_metrics.get("triangle_count"),
        "wall_thickness_stats": geometry_metrics.get("wall_thickness_stats"),
        "feature_flags": feature_flags,
        "geometry_metrics": geometry_metrics,
        "feature_map": feature_map,
        "manufacturing_decision": manufacturing_decision,
        "manufacturing_plan": manufacturing_plan,
        "cost_estimate": cost_estimate,
        "dfm_report": dfm_report,
        "engineering_report": engineering_report,
        "recommended_process": manufacturing_decision.get("recommended_process"),
        "estimated_unit_cost": cost_estimate.get("estimated_unit_cost"),
        "estimated_batch_cost": cost_estimate.get("estimated_batch_cost"),
        "dfm_risk": risks,
        "recommendations": recommendations + list(manufacturing_decision.get("recommended_changes") or []),
        "rule_version": "engineering_dfm.v1",
        "rule_explanations": explanations,
        "unavailable_reason": capability.get("unavailable_reason"),
    }


def _base_unavailable(
    *,
    file_id: str,
    capability: dict[str, Any],
    unavailable_reason: str | None = None,
) -> dict[str, Any]:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id=file_id,
        mode=capability.get("mode") or MODE_VISUAL_ONLY,
        source_type="analysis_unavailable",
        confidence=float(capability.get("confidence") or 0.0),
        bbox=None,
        volume=None,
        surface_area=None,
        part_count=None,
        triangle_count=None,
        metadata={"capability_status": capability.get("capability_status")},
    )
    feature_map = build_feature_map(
        mode=geometry_metrics["mode"],
        geometry_metrics=geometry_metrics,
        feature_flags={},
        source_signals={},
    )
    (
        manufacturing_decision,
        manufacturing_plan,
        cost_estimate,
    ) = _build_engineering_outputs(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )
    dfm_report = build_engineering_dfm_report(
        file_id=file_id,
        mode=str(capability.get("mode") or MODE_VISUAL_ONLY),
        confidence=float(capability.get("confidence") or 0.0),
        rule_version="engineering_dfm.v1",
        rule_explanations=[],
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        risk_analysis=[],
        recommendations=list(manufacturing_decision.get("recommended_changes") or []),
        capability_status=capability.get("capability_status"),
        unavailable_reason=unavailable_reason or capability.get("unavailable_reason"),
    )
    engineering_report = build_engineering_report(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=manufacturing_plan,
        cost_estimate=cost_estimate,
        dfm_report=dfm_report,
    )
    return {
        "file_id": file_id,
        "mode": capability.get("mode"),
        "confidence": float(capability.get("confidence") or 0.0),
        "capability_status": capability.get("capability_status"),
        "units": "mm",
        "volume": None,
        "surface_area": None,
        "bounding_box": None,
        "part_count": None,
        "triangle_count": None,
        "wall_thickness_stats": geometry_metrics.get("wall_thickness_stats"),
        "feature_flags": {},
        "geometry_metrics": geometry_metrics,
        "feature_map": feature_map,
        "manufacturing_decision": manufacturing_decision,
        "manufacturing_plan": manufacturing_plan,
        "cost_estimate": cost_estimate,
        "dfm_report": dfm_report,
        "engineering_report": engineering_report,
        "recommended_process": manufacturing_decision.get("recommended_process"),
        "estimated_unit_cost": cost_estimate.get("estimated_unit_cost"),
        "estimated_batch_cost": cost_estimate.get("estimated_batch_cost"),
        "dfm_risk": [],
        "recommendations": list(manufacturing_decision.get("recommended_changes") or []),
        "rule_version": "engineering_dfm.v1",
        "rule_explanations": [],
        "unavailable_reason": unavailable_reason or capability.get("unavailable_reason"),
    }


def _safe_filename(filename: str) -> str:
    token = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(filename or "upload.bin"))
    return token or "upload.bin"


def _thin_ratio(extents: list[float]) -> float:
    values = [abs(float(item)) for item in extents if float(item) > 0]
    if not values:
        return 0.0
    return min(values) / max(values)


def _build_engineering_outputs(
    *,
    geometry_metrics: dict[str, Any],
    feature_map: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manufacturing_decision = build_manufacturing_decision(
        mode=geometry_metrics["mode"],
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )
    manufacturing_plan = build_manufacturing_plan(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
    )
    cost_estimate = build_cost_estimate(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=manufacturing_plan,
    )
    return manufacturing_decision, manufacturing_plan, cost_estimate
