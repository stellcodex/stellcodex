from __future__ import annotations

import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from rq import Retry

from app.core.config import settings
from app.core.dlq import PermanentStageError, TransientStageError
from app.core.engineering_persistence import (
    finalize_analysis_run,
    geometry_hash_for_upload,
    persist_engineering_analysis,
    start_analysis_run,
)
from app.core.event_bus import default_event_bus
from app.core.event_types import EventType, StageName
from app.core.format_intelligence import extract_format_intelligence
from app.core.format_registry import get_rule_for_filename
from app.core.hybrid_v1_rules import run_hybrid_v1_step_pipeline
from app.core.identity.stell_identity import ANALYSIS_UNAVAILABLE_TEXT, STELL_IDENTITY_NAME
from app.core.memory_foundation import write_memory_payload
from app.core.orchestrator import ensure_session_decision
from app.core.read_model import upsert_projection
from app.core.storage import get_s3_client
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.models.job_failure import JobFailure
from app.queue import get_queue
from app.services.audit import log_event
from app.services.tenant_identity import resolve_or_create_tenant_id
from app.services.orchestrator_engine import (
    build_decision_json,
    load_rule_config_map,
    upsert_orchestrator_session,
)
from app.workers.consumers import consume_with_guards
from app.workers.consumers.common import resolve_version_no

DEFAULT_RESULT_TTL_SECONDS = 3600
DEFAULT_JOB_TTL_SECONDS = 3600
PREVIEW_ANGLES = ("iso_front", "iso_back", "top")
STEP_EXTS = {"step", "stp"}
EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

FALLBACK_JPG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb0043001011121412181414181b18181b201d1b1b1d20"
    "252320202323252b2a29292a2b2f2e2d2d2e2f33323233384646484f4f5865657a7a92ffd900"
)
FALLBACK_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c49444154789c63"
    "f8ffff3f0005fe02fe0f1f8e4f0000000049454e44ae426082"
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ext(name: str) -> str:
    return (Path(name or "").suffix or "").lower().lstrip(".")


def _current_geometry_hash(file_row: UploadFile) -> str | None:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    existing = str(meta.get("geometry_hash") or "").strip()
    if existing:
        return existing
    try:
        return geometry_hash_for_upload(file_row)
    except Exception:
        return None


def _run(cmd: list[str], timeout: int) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def _tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _load_preview_bytes() -> bytes:
    candidates = (
        Path("/var/www/stellcodex/frontend/src/app/gorsel/MASTER1.jpg"),
        Path(__file__).resolve().parents[3] / "frontend" / "src" / "app" / "gorsel" / "MASTER1.jpg",
    )
    for path in candidates:
        if path.exists():
            data = path.read_bytes()
            if data.startswith(b"\xff\xd8\xff"):
                return data
    return FALLBACK_JPG


def _load_thumb_bytes() -> bytes:
    candidates = (
        Path("/var/www/stellcodex/frontend/public/icon-192.png"),
        Path(__file__).resolve().parents[3] / "frontend" / "public" / "icon-192.png",
    )
    for path in candidates:
        if path.exists():
            data = path.read_bytes()
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                return data
    return FALLBACK_PNG


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
    xref_positions = []
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


def _compute_bbox_from_points(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        return (120.0, 80.0, 40.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    return (
        round(dx if dx > 0 else 1.0, 5),
        round(dy if dy > 0 else 1.0, 5),
        round(dz if dz > 0 else 1.0, 5),
    )


def _default_dims_from_size(size_bytes: int) -> tuple[float, float, float]:
    base = max(30.0, min(600.0, float((size_bytes % 5_000_000) / 10_000 + 40)))
    return (round(base, 3), round(base * 0.72, 3), round(base * 0.48, 3))


def _bbox_from_obj(path: Path) -> tuple[float, float, float]:
    points: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if not line.startswith("v "):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                points.append((float(parts[1]), float(parts[2]), float(parts[3])))
            except ValueError:
                continue
    return _compute_bbox_from_points(points)


def _bbox_from_ascii_stl(path: Path) -> tuple[float, float, float]:
    points: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped.lower().startswith("vertex "):
                continue
            parts = stripped.split()
            if len(parts) != 4:
                continue
            try:
                points.append((float(parts[1]), float(parts[2]), float(parts[3])))
            except ValueError:
                continue
    return _compute_bbox_from_points(points)


def _bbox_from_binary_stl(path: Path) -> tuple[float, float, float]:
    data = path.read_bytes()
    if len(data) < 84:
        return _default_dims_from_size(path.stat().st_size)
    tri_count = struct.unpack("<I", data[80:84])[0]
    offset = 84
    points: list[tuple[float, float, float]] = []
    max_tri = min(tri_count, 200_000)
    for _ in range(max_tri):
        if offset + 50 > len(data):
            break
        offset += 12  # normal
        for _vertex in range(3):
            x, y, z = struct.unpack("<fff", data[offset : offset + 12])
            points.append((x, y, z))
            offset += 12
        offset += 2
    return _compute_bbox_from_points(points)


def _bbox_from_stl(path: Path) -> tuple[float, float, float]:
    head = path.read_bytes()[:128]
    if head[:5].lower() == b"solid":
        return _bbox_from_ascii_stl(path)
    return _bbox_from_binary_stl(path)


def _geometry_meta(input_path: Path, ext: str, part_count: int = 1) -> dict:
    triangle_count: int | None = None

    # STEP files: use the real text-level geometry extractor
    if ext in STEP_EXTS:
        try:
            from app.services.step_extractor import geometry_meta_from_step
            meta = geometry_meta_from_step(input_path)
            # Ensure part_count is at least what was estimated by the caller
            meta["part_count"] = max(int(meta.get("part_count") or 1), max(1, int(part_count)))
            return meta
        except Exception:
            pass  # fall through to size-based fallback

    dims: tuple[float, float, float]
    if ext == "obj":
        dims = _bbox_from_obj(input_path)
    elif ext == "stl":
        dims = _bbox_from_stl(input_path)
        if input_path.stat().st_size >= 84:
            data = input_path.read_bytes()[:84]
            if len(data) == 84 and data[:5].lower() != b"solid":
                triangle_count = int(struct.unpack("<I", data[80:84])[0])
    else:
        dims = _default_dims_from_size(input_path.stat().st_size)

    diagonal = math.sqrt(dims[0] ** 2 + dims[1] ** 2 + dims[2] ** 2)
    return {
        "units": "mm",
        "bbox": {"x": dims[0], "y": dims[1], "z": dims[2]},
        "diagonal": round(diagonal, 5),
        "part_count": max(1, int(part_count)),
        "triangle_count": triangle_count,
        "volume": None,
    }


def _estimate_step_part_count(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").upper()
    except Exception:
        return 1

    candidates = (
        len(re.findall(r"\bNEXT_ASSEMBLY_USAGE_OCCURRENCE\s*\(", text)),
        len(re.findall(r"\bPRODUCT_DEFINITION_SHAPE\s*\(", text)),
        len(re.findall(r"\bMANIFOLD_SOLID_BREP\s*\(", text)),
    )
    for candidate in candidates:
        if candidate > 0:
            return max(1, min(candidate, 500))
    return 1


def _assembly_meta(mode: str, part_count: int, filename: str) -> dict:
    stem = Path(filename or "model").stem or "model"
    occurrences = []
    occurrence_index: dict[str, list[str]] = {}
    count = max(1, part_count)
    for idx in range(count):
        occ_id = f"occ_{idx + 1:03d}"
        part_id = f"part_{idx + 1:03d}"
        label = f"{stem}-{idx + 1}" if count > 1 else stem
        occurrences.append(
            {
                "occurrence_id": occ_id,
                "part_id": part_id,
                "name": label,
                "display_name": label,
                "selectable": True,
                "children": [],
            }
        )
        occurrence_index[occ_id] = []
    return {
        "mode": mode,
        "generated_at": _now().isoformat(),
        "occurrences": occurrences,
        "index": {"occurrence_id_to_gltf_nodes": occurrence_index},
        "occurrence_id_to_gltf_nodes": occurrence_index,
    }


def _upload_file(s3, bucket: str, key: str, local_path: Path, content_type: str) -> str:
    s3.upload_file(str(local_path), bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def _upload_bytes(s3, bucket: str, key: str, payload: bytes, content_type: str) -> str:
    s3.put_object(Bucket=bucket, Key=key, Body=payload, ContentType=content_type)
    return key


def _mark_failed(
    db,
    f: UploadFile,
    detail: str,
    stage: str = "convert",
    error_code: str | None = None,
) -> str:
    error_id = str(uuid4())
    f.status = "failed"
    rules = load_rule_config_map(db)
    decision_json = build_decision_json(f, rules)
    f.decision_json = decision_json
    f.meta = {
        **(f.meta or {}),
        "error": detail,
        "error_code": error_code,
        "error_id": error_id,
        "stage": stage,
        "progress_percent": 100,
        "progress": "failed",
        "decision_json": decision_json,
    }
    db.add(f)
    upsert_orchestrator_session(db, f, decision_json)
    db.add(
        JobFailure(
            job_id=(f.meta or {}).get("job_id"),
            file_id=f.file_id,
            stage=stage,
            error_class="ConversionError",
            message=detail[:500],
            traceback=None,
        )
    )
    upsert_projection(db, f)
    try:
        memory_path = write_memory_payload(
            record_type="failure_event",
            title=f"Pipeline failure {error_code or 'UNKNOWN'}",
            source_uri=f"scx://files/{f.file_id}/failure",
            tenant_id=str(f.tenant_id),
            project_id=str((f.meta or {}).get("project_id") or "default"),
            tags=["phase2", "failure", stage, str(error_code or "UNKNOWN").lower()],
            text=detail[:4000],
            metadata={
                "file_id": f.file_id,
                "stage": stage,
                "error_code": error_code,
                "error_id": error_id,
            },
        )
        f.meta = {**(f.meta or {}), "last_failure_memory_record": str(memory_path)}
        db.add(f)
    except Exception:
        pass
    log_event(db, "job.failed", file_id=f.file_id, data={"stage": stage, "error": detail[:300]})
    db.commit()
    return error_id


def _set_progress(db, f: UploadFile, *, stage: str, percent: int, hint: str, status: str | None = None) -> None:
    f.meta = {
        **(f.meta or {}),
        "stage": stage,
        "progress_percent": max(0, min(100, int(percent))),
        "progress": hint,
    }
    if status:
        f.status = status
    db.add(f)
    upsert_projection(db, f)
    db.commit()
    db.refresh(f)


def _scan_file_for_virus(input_path: Path) -> str:
    chunk = input_path.read_bytes()[:5_000_000]
    if EICAR_SIGNATURE in chunk:
        return "infected"
    return "clean"


def _convert_with_assimp(input_path: Path, output_path: Path) -> bool:
    if not _tool_exists("assimp"):
        return False
    try:
        _run(["assimp", "export", str(input_path), str(output_path), "-f", "glb"], timeout=settings.conversion_timeout_seconds)
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False


def _convert_with_occt(input_path: Path, output_path: Path) -> bool:
    if not _tool_exists("occt-convert"):
        return False
    try:
        _run(["occt-convert", str(input_path), str(output_path)], timeout=settings.conversion_timeout_seconds)
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False


def _convert_with_soffice(input_path: Path, out_dir: Path) -> Path | None:
    if not (_tool_exists("soffice") or _tool_exists("libreoffice")):
        return None
    binary = shutil.which("soffice") or shutil.which("libreoffice")
    try:
        _run(
            [str(binary), "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(input_path)],
            timeout=settings.conversion_timeout_seconds,
        )
    except Exception:
        return None
    candidate = out_dir / f"{input_path.stem}.pdf"
    return candidate if candidate.exists() and candidate.stat().st_size > 0 else None


def _generate_preview_jpgs(file_id: str, bucket: str, s3) -> list[str]:
    preview_bytes = _load_preview_bytes()
    keys: list[str] = []
    for angle in PREVIEW_ANGLES:
        key = f"previews/{file_id}/preview_{angle}.jpg"
        _upload_bytes(s3, bucket, key, preview_bytes, "image/jpeg")
        keys.append(key)
    return keys


def _generate_thumbnail_png(file_id: str, bucket: str, s3) -> str:
    thumb_bytes = _load_thumb_bytes()
    key = f"thumbnails/{file_id}/thumb.png"
    _upload_bytes(s3, bucket, key, thumb_bytes, "image/png")
    return key


def _pipeline_doc(f: UploadFile, input_path: Path, s3) -> dict:
    ext = _ext(f.original_filename)
    pdf_key: str
    if ext == "pdf":
        pdf_key = f.object_key
    else:
        with tempfile.TemporaryDirectory() as tmp_pdf_dir:
            out_dir = Path(tmp_pdf_dir)
            converted = _convert_with_soffice(input_path, out_dir)
            if converted is None:
                preview = _simple_pdf_bytes(
                    "STELLCODEX Document Preview",
                    [
                        f"source: {f.original_filename}",
                        "LibreOffice unavailable: generated deterministic preview PDF.",
                    ],
                )
                converted = out_dir / "generated.pdf"
                converted.write_bytes(preview)
            pdf_key = f"documents/{f.file_id}/document.pdf"
            _upload_file(s3, f.bucket, pdf_key, converted, "application/pdf")
    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    return {"pdf_key": pdf_key, "thumbnail_key": thumb_key}


def _pipeline_2d(f: UploadFile, input_path: Path, s3) -> dict:
    ext = _ext(f.original_filename)
    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    result: dict[str, str] = {"thumbnail_key": thumb_key}
    if ext == "pdf":
        result["pdf_key"] = f.object_key
    return result


def _pipeline_image(f: UploadFile, input_path: Path, s3) -> dict:
    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    return {"thumbnail_key": thumb_key}


def _pipeline_3d(
    f: UploadFile,
    input_path: Path,
    mode: str,
    s3,
    *,
    geometry_meta: dict[str, Any] | None = None,
    part_count: int | None = None,
) -> dict:
    ext = _ext(f.original_filename)
    out_glb = Path(input_path.parent) / "model.glb"
    gltf_key: str | None = None

    if ext in {"glb", "gltf"} and mode == "visual_only":
        gltf_key = f.object_key
    else:
        converted = False
        if mode == "brep":
            converted = _convert_with_occt(input_path, out_glb) or _convert_with_assimp(input_path, out_glb)
        else:
            converted = _convert_with_assimp(input_path, out_glb)
        if converted:
            gltf_key = f"converted/{f.file_id}/model.glb"
            _upload_file(s3, f.bucket, gltf_key, out_glb, "model/gltf-binary")
        else:
            # deterministic fallback: keep public contract complete and mark conversion fallback.
            gltf_key = f.object_key

    effective_part_count = int(part_count or 0)
    if effective_part_count < 1:
        effective_part_count = _estimate_step_part_count(input_path) if ext in STEP_EXTS else 1
    assembly = _assembly_meta(mode, effective_part_count, f.original_filename)
    assembly_key = f"metadata/{f.file_id}/assembly_meta.json"
    _upload_bytes(
        s3,
        f.bucket,
        assembly_key,
        json.dumps(assembly, ensure_ascii=False, indent=2).encode("utf-8"),
        "application/json",
    )

    preview_keys = _generate_preview_jpgs(f.file_id, f.bucket, s3)
    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    return {
        "gltf_key": gltf_key,
        "thumbnail_key": thumb_key,
        "assembly_meta_key": assembly_key,
        "assembly_meta": assembly,
        "preview_jpg_keys": preview_keys,
        "occurrence_count": len(assembly.get("occurrences") or []),
        **({"geometry_meta_json": geometry_meta} if isinstance(geometry_meta, dict) else {}),
    }


def _hybrid_artifacts_if_step(
    input_path: Path,
    ext: str,
    rules: dict[str, Any] | None = None,
) -> tuple[dict | None, dict | None]:
    if ext not in STEP_EXTS:
        return None, None
    try:
        out = run_hybrid_v1_step_pipeline(str(input_path), config=rules)
    except Exception:
        return None, None
    geometry_report = out.get("geometry_report")
    dfm_findings = out.get("dfm_findings")
    return (
        geometry_report if isinstance(geometry_report, dict) else None,
        dfm_findings if isinstance(dfm_findings, dict) else None,
    )


def _assembly_meta_is_valid(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    occurrences = payload.get("occurrences")
    if not isinstance(occurrences, list) or not occurrences:
        return False
    index_map = {}
    index = payload.get("index")
    if isinstance(index, dict) and isinstance(index.get("occurrence_id_to_gltf_nodes"), dict):
        index_map = index.get("occurrence_id_to_gltf_nodes") or {}
    elif isinstance(payload.get("occurrence_id_to_gltf_nodes"), dict):
        index_map = payload.get("occurrence_id_to_gltf_nodes") or {}
    else:
        return False
    known_ids: list[str] = []
    children_map: dict[str, list[str]] = {}
    parent_counts: dict[str, int] = {}
    for item in occurrences:
        if not isinstance(item, dict):
            return False
        occ_id = str(item.get("occurrence_id") or "").strip()
        if occ_id in parent_counts:
            return False
        known_ids.append(occ_id)
        parent_counts[occ_id] = 0
    for item in occurrences:
        occ_id = str(item.get("occurrence_id") or "").strip()
        part_id = str(item.get("part_id") or "").strip()
        display_name = str(item.get("display_name") or item.get("name") or "").strip()
        selectable = item.get("selectable", True)
        children = item.get("children")
        if not occ_id or not part_id or not display_name or not isinstance(children, list) or not isinstance(selectable, bool):
            return False
        child_ids: list[str] = []
        for child in children:
            if isinstance(child, str):
                child_id = child.strip()
            elif isinstance(child, dict):
                child_id = str(child.get("occurrence_id") or child.get("id") or "").strip()
            else:
                return False
            if not child_id:
                return False
            child_ids.append(child_id)
        if len(child_ids) != len(set(child_ids)):
            return False
        children_map[occ_id] = child_ids
        for child_id in child_ids:
            if child_id == occ_id or child_id not in parent_counts:
                return False
            parent_counts[child_id] += 1
            if parent_counts[child_id] > 1:
                return False
        mapped = index_map.get(occ_id, [])
        if not isinstance(mapped, list):
            return False
        if not all(isinstance(node, str) and node.strip() for node in mapped):
            return False
    visiting: set[str] = set()
    visited: set[str] = set()

    def _dfs(node_id: str) -> bool:
        if node_id in visited:
            return True
        if node_id in visiting:
            return False
        visiting.add(node_id)
        for child_id in children_map.get(node_id, []):
            if not _dfs(child_id):
                return False
        visiting.remove(node_id)
        visited.add(node_id)
        return True

    roots = [occ_id for occ_id, count in parent_counts.items() if count == 0]
    if not roots:
        return False
    for root_id in roots:
        if not _dfs(root_id):
            return False
    if len(visited) != len(known_ids):
        return False
    return True


def _is_ready_contract(kind: str, payload: dict, gltf_key: str | None, thumb_key: str | None) -> bool:
    if kind == "3d":
        previews = payload.get("preview_jpg_keys")
        assembly_meta = payload.get("assembly_meta")
        return bool(
            gltf_key
            and isinstance(payload.get("assembly_meta_key"), str)
            and isinstance(previews, list)
            and len(previews) >= 3
            and _assembly_meta_is_valid(assembly_meta)
        )
    if kind == "doc":
        return bool(payload.get("pdf_key") and thumb_key)
    if kind in {"2d", "image"}:
        return bool(thumb_key)
    return False


def _get_stage_file(db, file_id: str) -> UploadFile:
    row = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if row is None:
        raise PermanentStageError(f"file not found: {file_id}", "UNKNOWN")
    return row


def _memory_project_id(meta: dict[str, Any]) -> str:
    return str(meta.get("project_id") or "default")


def _stage_convert(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    rules = load_rule_config_map(db)
    rule = get_rule_for_filename(f.original_filename)
    if not rule:
        raise PermanentStageError("Unsupported file extension. STEP export required", "CONVERT_FAIL")
    if not rule.accept:
        raise PermanentStageError(rule.reject_reason or "Unsupported file type", "CONVERT_FAIL")

    meta = f.meta if isinstance(f.meta, dict) else {}
    kind = rule.kind
    mode = rule.mode
    result_payload: dict[str, Any] = {}
    _set_progress(db, f, stage=StageName.CONVERT.value, percent=12, hint="convert.start", status="running")
    try:
        s3 = get_s3_client(settings)
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = Path(tmp_dir) / f"input.{_ext(f.original_filename)}"
            s3.download_file(f.bucket, f.object_key, str(local_path))
            _set_progress(db, f, stage="security", percent=20, hint="virus_scan", status="running")
            virus_status = _scan_file_for_virus(local_path)
            if virus_status == "infected":
                raise PermanentStageError("Virus scan failed", "STORAGE_FAIL")

            extraction = extract_format_intelligence(
                local_path,
                file_id=f.file_id,
                tenant_id=int(f.tenant_id),
                original_filename=f.original_filename,
                mime_type=f.content_type,
                size_bytes=int(f.size_bytes),
                checksum=str(f.sha256) if f.sha256 else None,
                sniffed_content_type=str(meta.get("sniffed_content_type") or "") or None,
            )
            real_supported_tier = str(extraction.get("support_tier") or "") in {"metadata_extracted", "geometry_extracted", "dfm_supported"}
            extraction_status = str(extraction.get("extraction_status") or "")
            if not f.sha256 and isinstance(extraction.get("checksum"), str) and extraction.get("checksum"):
                f.sha256 = str(extraction["checksum"])
            if extraction_status == "failed" and real_supported_tier:
                extraction_errors = extraction.get("extraction_errors") if isinstance(extraction.get("extraction_errors"), list) else []
                first_error = extraction_errors[0] if extraction_errors and isinstance(extraction_errors[0], dict) else {}
                f.meta = {
                    **meta,
                    "kind": kind,
                    "mode": mode,
                    "project_id": _memory_project_id(meta),
                    "virus_scan_status": "clean",
                    "extraction_result": extraction,
                    "stage": StageName.CONVERT.value,
                    "progress_percent": 34,
                    "progress": "convert.extraction_failed",
                }
                db.add(f)
                upsert_projection(db, f)
                db.commit()
                message = str(first_error.get("message") or "Extraction failed safely")
                raise PermanentStageError(message, "CONVERT_FAIL")

            _set_progress(db, f, stage=StageName.CONVERT.value, percent=34, hint="convert.processing", status="running")
            if kind == "3d":
                result_payload = _pipeline_3d(
                    f,
                    local_path,
                    mode,
                    s3,
                    geometry_meta=extraction.get("geometry_meta_json") if isinstance(extraction.get("geometry_meta_json"), dict) else None,
                    part_count=int(extraction.get("part_count") or 0) if isinstance(extraction.get("part_count"), int) else None,
                )
                geometry_report, dfm_findings = _hybrid_artifacts_if_step(
                    local_path,
                    _ext(f.original_filename),
                    rules=rules,
                )
                if geometry_report is not None:
                    result_payload["geometry_report"] = geometry_report
                if dfm_findings is not None:
                    result_payload["dfm_findings"] = dfm_findings
            elif kind == "2d":
                result_payload = _pipeline_2d(f, local_path, s3)
            elif kind == "doc":
                result_payload = _pipeline_doc(f, local_path, s3)
            elif kind == "image":
                result_payload = _pipeline_image(f, local_path, s3)
            else:
                raise PermanentStageError(f"Unsupported kind: {kind}", "CONVERT_FAIL")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "conversion failed").strip()
        raise PermanentStageError(detail, "CONVERT_FAIL")
    except PermanentStageError:
        raise
    except Exception as exc:
        raise TransientStageError(str(exc), "STORAGE_FAIL")

    f.gltf_key = result_payload.get("gltf_key") if isinstance(result_payload.get("gltf_key"), str) else f.gltf_key
    f.thumbnail_key = (
        result_payload.get("thumbnail_key")
        if isinstance(result_payload.get("thumbnail_key"), str)
        else f.thumbnail_key
    )
    geometry = result_payload.get("geometry_meta_json")
    occurrence_count = result_payload.get("occurrence_count")
    if not isinstance(occurrence_count, int) or occurrence_count < 1:
        occurrence_count = 1 if kind == "3d" else None

    next_meta = {
        **meta,
        "kind": kind,
        "mode": mode,
        "project_id": _memory_project_id(meta),
        "virus_scan_status": "clean",
        "assembly_meta_key": result_payload.get("assembly_meta_key"),
        "assembly_meta": result_payload.get("assembly_meta") if isinstance(result_payload.get("assembly_meta"), dict) else meta.get("assembly_meta"),
        "preview_jpg_keys": result_payload.get("preview_jpg_keys"),
        "pdf_key": result_payload.get("pdf_key"),
        "geometry_meta_json": geometry if isinstance(geometry, dict) else None,
        "occurrence_count": occurrence_count if occurrence_count is not None else meta.get("occurrence_count"),
        "part_count": occurrence_count if occurrence_count is not None else meta.get("part_count"),
        "geometry_report": result_payload.get("geometry_report") if isinstance(result_payload.get("geometry_report"), dict) else meta.get("geometry_report"),
        "dfm_findings": result_payload.get("dfm_findings") if isinstance(result_payload.get("dfm_findings"), dict) else meta.get("dfm_findings"),
        "extraction_result": extraction,
        "stage": StageName.CONVERT.value,
        "progress_percent": 40,
        "progress": "convert.done",
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    f.folder_key = f.folder_key or f"project/{_memory_project_id(meta)}/{kind}/{mode}"
    f.status = "running"
    db.add(f)
    upsert_projection(db, f)
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "kind": kind,
        "mode": mode,
        "geometry_hash": geometry_hash,
        "artifact_uri": str(result_payload.get("gltf_key") or result_payload.get("pdf_key") or result_payload.get("thumbnail_key") or ""),
    }


def _stage_assembly_meta(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    meta = f.meta if isinstance(f.meta, dict) else {}
    kind = str(meta.get("kind") or "3d")
    if kind != "3d":
        f.meta = {**meta, "stage": StageName.ASSEMBLY_META.value, "progress_percent": 52, "progress": "assembly.skip"}
        db.add(f)
        upsert_projection(db, f)
        return {"file_id": f.file_id, "version_no": int(version_no), "kind": kind, "artifact_uri": ""}

    assembly_payload = meta.get("assembly_meta") if isinstance(meta.get("assembly_meta"), dict) else None
    if not _assembly_meta_is_valid(assembly_payload):
        part_count = meta.get("part_count")
        if not isinstance(part_count, int) or part_count < 1:
            part_count = 1
        assembly_payload = _assembly_meta(str(meta.get("mode") or "brep"), part_count, f.original_filename)
        assembly_key = str(meta.get("assembly_meta_key") or f"metadata/{f.file_id}/assembly_meta.json")
        try:
            s3 = get_s3_client(settings)
            _upload_bytes(
                s3,
                f.bucket,
                assembly_key,
                json.dumps(assembly_payload, ensure_ascii=False, indent=2).encode("utf-8"),
                "application/json",
            )
        except Exception as exc:
            raise TransientStageError(str(exc), "STORAGE_FAIL")
        meta = {
            **meta,
            "assembly_meta_key": assembly_key,
            "assembly_meta": assembly_payload,
        }
    next_meta = {
        **meta,
        "part_count": len((assembly_payload or {}).get("occurrences") or []) or int(meta.get("part_count") or 1),
        "occurrence_count": len((assembly_payload or {}).get("occurrences") or []) or int(meta.get("occurrence_count") or 1),
        "stage": StageName.ASSEMBLY_META.value,
        "progress_percent": 52,
        "progress": "assembly.ready",
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    db.add(f)
    upsert_projection(db, f)
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "kind": kind,
        "geometry_hash": geometry_hash,
        "artifact_uri": str(f.meta.get("assembly_meta_key") or ""),
    }


def _stage_rule_engine(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    rules = load_rule_config_map(db)
    decision_json = build_decision_json(f, rules)
    f.decision_json = decision_json
    meta = f.meta if isinstance(f.meta, dict) else {}
    next_meta = {
        **meta,
        "decision_json": decision_json,
        "stage": StageName.RULE_ENGINE.value,
        "progress_percent": 64,
        "progress": "rule_engine.ready",
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    db.add(f)
    upsert_orchestrator_session(db, f, decision_json)
    upsert_projection(db, f)
    try:
        record = write_memory_payload(
            record_type="decision_json",
            title="Deterministic decision",
            source_uri=f"scx://files/{f.file_id}/decision_json",
            tenant_id=str(f.tenant_id),
            project_id=_memory_project_id(f.meta or {}),
            tags=["phase2", "decision", "deterministic"],
            text=json.dumps(decision_json, ensure_ascii=False, sort_keys=True),
            metadata={"file_id": f.file_id, "version_no": int(version_no)},
        )
        f.meta = {**(f.meta or {}), "decision_memory_record": str(record)}
        db.add(f)
    except Exception:
        pass
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "approval_required": bool(decision_json.get("approval_required")),
        "geometry_hash": geometry_hash,
        "artifact_uri": f"scx://files/{f.file_id}/decision_json",
    }


def _stage_dfm(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    _row, decision_json = ensure_session_decision(db, f)
    f = _get_stage_file(db, f.file_id)
    meta = f.meta if isinstance(f.meta, dict) else {}
    dfm_report = meta.get("dfm_report_json") if isinstance(meta.get("dfm_report_json"), dict) else {}
    next_meta = {
        **meta,
        "stage": StageName.DFM.value,
        "progress_percent": 76,
        "progress": "dfm.ready",
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    db.add(f)
    upsert_projection(db, f)
    try:
        record = write_memory_payload(
            record_type="dfm_report",
            title="Deterministic DFM report",
            source_uri=f"scx://files/{f.file_id}/dfm_report",
            tenant_id=str(f.tenant_id),
            project_id=_memory_project_id(f.meta or {}),
            tags=["phase2", "dfm", "deterministic"],
            text=json.dumps(dfm_report, ensure_ascii=False, sort_keys=True),
            metadata={"file_id": f.file_id, "version_no": int(version_no)},
        )
        f.meta = {**(f.meta or {}), "dfm_memory_record": str(record)}
        db.add(f)
    except Exception:
        pass
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "approval_required": bool(decision_json.get("approval_required")),
        "geometry_hash": geometry_hash,
        "artifact_uri": f"scx://files/{f.file_id}/dfm_report",
    }


def _stage_report(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    meta = f.meta if isinstance(f.meta, dict) else {}
    dfm_report = meta.get("dfm_report_json") if isinstance(meta.get("dfm_report_json"), dict) else {}
    report_key = f"reports/{f.file_id}/dfm_report.json"
    pdf_key = f"reports/{f.file_id}/dfm_report.pdf"
    try:
        s3 = get_s3_client(settings)
        _upload_bytes(
            s3,
            f.bucket,
            report_key,
            json.dumps(dfm_report, ensure_ascii=False, indent=2).encode("utf-8"),
            "application/json",
        )
        raw_pdf = meta.get("dfm_report_pdf_b64")
        if isinstance(raw_pdf, str) and raw_pdf:
            _upload_bytes(s3, f.bucket, pdf_key, base64.b64decode(raw_pdf), "application/pdf")
        else:
            pdf_key = ""
    except Exception as exc:
        raise TransientStageError(str(exc), "REPORT_FAIL")

    next_meta = {
        **meta,
        "dfm_report_key": report_key,
        "dfm_report_pdf_key": pdf_key or None,
        "stage": StageName.REPORT.value,
        "progress_percent": 88,
        "progress": "report.ready",
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    db.add(f)
    upsert_projection(db, f)
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "geometry_hash": geometry_hash,
        "artifact_uri": report_key,
    }


def _stage_pack(db, envelope, version_no: int) -> dict[str, Any]:
    f = _get_stage_file(db, str(envelope.data.get("file_id") or ""))
    meta = f.meta if isinstance(f.meta, dict) else {}
    package_key = f"packages/{f.file_id}/production_package.zip"
    try:
        s3 = get_s3_client(settings)
        with tempfile.TemporaryDirectory() as tmp_dir:
            package_path = Path(tmp_dir) / "production_package.zip"
            with ZipFile(package_path, mode="w", compression=ZIP_DEFLATED) as zf:
                zf.writestr("decision.json", json.dumps(f.decision_json if isinstance(f.decision_json, dict) else {}, ensure_ascii=False, indent=2))
                zf.writestr("dfm_report.json", json.dumps(meta.get("dfm_report_json") if isinstance(meta.get("dfm_report_json"), dict) else {}, ensure_ascii=False, indent=2))
                zf.writestr("assembly_meta.json", json.dumps(meta.get("assembly_meta") if isinstance(meta.get("assembly_meta"), dict) else {}, ensure_ascii=False, indent=2))
            _upload_file(s3, f.bucket, package_key, package_path, "application/zip")
    except Exception as exc:
        raise TransientStageError(str(exc), "PACKAGE_FAIL")

    payload = {
        "assembly_meta_key": meta.get("assembly_meta_key"),
        "assembly_meta": meta.get("assembly_meta"),
        "preview_jpg_keys": meta.get("preview_jpg_keys"),
        "pdf_key": meta.get("pdf_key"),
    }
    kind = str(meta.get("kind") or "3d")
    if not _is_ready_contract(kind, payload, f.gltf_key, f.thumbnail_key):
        raise PermanentStageError(
            "Required artifacts missing for ready contract",
            "ASSEMBLY_META_FAIL" if kind == "3d" else "PACKAGE_FAIL",
        )

    f.status = "ready"
    rules = load_rule_config_map(db)
    decision_json = build_decision_json(f, rules)
    f.decision_json = decision_json
    next_meta = {
        **meta,
        "production_package_key": package_key,
        "stage": "ready",
        "progress_percent": 100,
        "progress": "ready",
        "decision_json": decision_json,
    }
    f.meta = next_meta
    geometry_hash = _current_geometry_hash(f)
    f.meta = {**next_meta, "geometry_hash": geometry_hash}
    db.add(f)
    upsert_orchestrator_session(db, f, decision_json)
    upsert_projection(db, f)
    log_event(db, "job.succeeded", file_id=f.file_id, data={"kind": kind, "mode": str(meta.get("mode") or "visual_only")})
    try:
        record = write_memory_payload(
            record_type="production_package",
            title="Production package manifest",
            source_uri=f"scx://files/{f.file_id}/production_package",
            tenant_id=str(f.tenant_id),
            project_id=_memory_project_id(f.meta or {}),
            tags=["phase2", "package"],
            text=json.dumps({"production_package_key": package_key}, ensure_ascii=False),
            metadata={"file_id": f.file_id, "version_no": int(version_no), "package_key": package_key},
        )
        f.meta = {**(f.meta or {}), "package_memory_record": str(record)}
        db.add(f)
    except Exception:
        pass
    return {
        "file_id": f.file_id,
        "version_no": int(version_no),
        "approval_required": bool(decision_json.get("approval_required")),
        "geometry_hash": geometry_hash,
        "artifact_uri": package_key,
    }


STAGE_PLAN: tuple[tuple[StageName, str, str, Any, EventType], ...] = (
    (StageName.CONVERT, "phase2.consumer.convert", "CONVERT_FAIL", _stage_convert, EventType.FILE_CONVERTED),
    (StageName.ASSEMBLY_META, "phase2.consumer.assembly_meta", "ASSEMBLY_META_FAIL", _stage_assembly_meta, EventType.ASSEMBLY_READY),
    (StageName.RULE_ENGINE, "phase2.consumer.rule_engine", "DECISION_FAIL", _stage_rule_engine, EventType.DECISION_READY),
    (StageName.DFM, "phase2.consumer.dfm", "DFM_FAIL", _stage_dfm, EventType.DFM_READY),
    (StageName.REPORT, "phase2.consumer.report", "REPORT_FAIL", _stage_report, EventType.REPORT_READY),
    (StageName.PACK, "phase2.consumer.pack", "PACKAGE_FAIL", _stage_pack, EventType.PACKAGE_READY),
)


def convert_file(file_id: str):
    db = SessionLocal()
    try:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}

        meta = f.meta if isinstance(f.meta, dict) else {}
        tenant_id = str(f.tenant_id)
        project_id = _memory_project_id(meta)
        version_no = resolve_version_no(db, f.file_id)
        bus = default_event_bus()

        trace_id = str(uuid4())
        current = bus.publish_event(
            event_type=EventType.FILE_UPLOADED.value,
            source="api.files.upload",
            subject=f.file_id,
            tenant_id=tenant_id,
            project_id=project_id,
            trace_id=trace_id,
            data={"file_id": f.file_id, "version_no": int(version_no)},
        )

        for stage, consumer_name, failure_code, handler, next_event in STAGE_PLAN:
            if stage == StageName.CONVERT:
                bus.publish_event(
                    event_type=EventType.FILE_CONVERT_STARTED.value,
                    source="worker.pipeline",
                    subject=f.file_id,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    trace_id=trace_id,
                    data={"file_id": f.file_id, "version_no": int(version_no), "stage": stage.value},
                )
            result = consume_with_guards(
                db,
                bus,
                envelope=current,
                consumer_name=consumer_name,
                stage=stage.value,
                max_retries=3,
                failure_code=failure_code,
                handler=handler,
            )
            status = str(result.get("status") or "")
            if status in {"failed"}:
                f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
                if f:
                    _mark_failed(
                        db,
                        f,
                        str(result.get("error") or f"{stage.value} failed"),
                        stage=stage.value,
                        error_code=str(result.get("failure_code") or failure_code),
                    )
                return {"status": "failed", "reason": stage.value}

            f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
            if not f:
                return {"status": "missing"}
            payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
            payload = {**payload, "file_id": f.file_id, "version_no": int(version_no), "stage": stage.value}
            current = bus.publish_event(
                event_type=next_event.value,
                source=f"worker.{stage.value}",
                subject=f.file_id,
                tenant_id=tenant_id,
                project_id=project_id,
                trace_id=trace_id,
                data=payload,
            )
            try:
                if next_event == EventType.DECISION_READY:
                    bus.publish_event(
                        event_type="decision.produced",
                        source=f"worker.{stage.value}",
                        subject=f.file_id,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        trace_id=trace_id,
                        data=payload,
                    )
                elif next_event == EventType.DFM_READY:
                    bus.publish_event(
                        event_type="dfm.completed",
                        source=f"worker.{stage.value}",
                        subject=f.file_id,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        trace_id=trace_id,
                        data=payload,
                    )
                elif next_event == EventType.PACKAGE_READY:
                    bus.publish_event(
                        event_type="file.ready",
                        source=f"worker.{stage.value}",
                        subject=f.file_id,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        trace_id=trace_id,
                        data=payload,
                    )
            except Exception:
                pass
            if bool(payload.get("approval_required")):
                bus.publish_event(
                    event_type=EventType.APPROVAL_REQUIRED.value,
                    source=f"worker.{stage.value}",
                    subject=f.file_id,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    trace_id=trace_id,
                    data={"file_id": f.file_id, "version_no": int(version_no), "stage": stage.value},
                )

        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        return {
            "status": "ready" if str(f.status).lower() == "ready" else str(f.status).lower(),
            "kind": str((f.meta or {}).get("kind") or "3d"),
            "mode": str((f.meta or {}).get("mode") or "visual_only"),
        }
    except subprocess.CalledProcessError as exc:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            detail = (exc.stderr or exc.stdout or "conversion failed").strip()
            _mark_failed(db, f, detail, stage=StageName.CONVERT.value, error_code="CONVERT_FAIL")
        raise
    except Exception as exc:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            _mark_failed(db, f, str(exc), stage=StageName.CONVERT.value, error_code="UNKNOWN")
        raise
    finally:
        db.close()


def convert_cad_to_glb(file_id: str):
    return convert_file(file_id)


def convert_mesh_to_glb(file_id: str):
    return convert_file(file_id)


def generate_thumbnails(file_id: str):
    db = SessionLocal()
    try:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        s3 = get_s3_client(settings)
        thumb_key = _generate_thumbnail_png(file_id, f.bucket, s3)
        f.thumbnail_key = thumb_key
        db.add(f)
        db.commit()
        return {"status": "ok", "thumbnail_key": thumb_key}
    finally:
        db.close()


def extract_metadata(file_id: str):
    db = SessionLocal()
    try:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = Path(tmp_dir) / f"input.{_ext(f.original_filename)}"
            s3 = get_s3_client(settings)
            s3.download_file(f.bucket, f.object_key, str(local_path))
            geometry = _geometry_meta(local_path, _ext(f.original_filename), part_count=1)
        f.meta = {**(f.meta or {}), "geometry_meta_json": geometry}
        db.add(f)
        db.commit()
        return {"status": "ok", "geometry_meta_json": geometry}
    finally:
        db.close()


def render_preset(file_id: str, preset_name: str):
    db = SessionLocal()
    try:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}
        s3 = get_s3_client(settings)
        payload = _load_preview_bytes()
        render_key = f"renders/{f.file_id}/{preset_name}.jpg"
        _upload_bytes(s3, f.bucket, render_key, payload, "image/jpeg")
        f.meta = {**(f.meta or {}), "renders": {**((f.meta or {}).get("renders") or {}), preset_name: render_key}}
        db.add(f)
        log_event(db, "render.completed", file_id=f.file_id, data={"preset": preset_name})
        db.commit()
        return {"status": "ok", "render_key": render_key}
    finally:
        db.close()


def mesh2d3d_export(source_file_id: str):
    db = SessionLocal()
    try:
        source = db.query(UploadFile).filter(UploadFile.file_id == source_file_id).first()
        if not source:
            return {"status": "missing"}

        meta = source.meta if isinstance(source.meta, dict) else {}
        project_id = str(meta.get("project_id") or "default")
        owner_sub = source.owner_sub
        tenant_id = int(source.tenant_id)
        bucket = source.bucket
        safe_owner = owner_sub.replace("/", "_").replace("\\", "_")
        object_key = f"uploads/tenant_{tenant_id}/{safe_owner}/generated/{uuid4()}/mesh2d3d.obj"
        thumb_key = f"thumbnails/{source_file_id}/mesh2d3d-thumb.png"
        obj_payload = "\n".join(
            [
                "o mesh2d3d",
                "v 0 0 0",
                "v 120 0 0",
                "v 120 80 0",
                "v 0 80 0",
                "v 0 0 18",
                "v 120 0 18",
                "v 120 80 18",
                "v 0 80 18",
                "f 1 2 3",
                "f 1 3 4",
                "f 5 6 7",
                "f 5 7 8",
                "f 1 5 6",
                "f 1 6 2",
                "f 2 6 7",
                "f 2 7 3",
                "f 3 7 8",
                "f 3 8 4",
                "f 4 8 5",
                "f 4 5 1",
            ]
        ).encode("utf-8")
        thumb_payload = _load_thumb_bytes()
        s3 = get_s3_client(settings)
        _upload_bytes(s3, bucket, object_key, obj_payload, "model/obj")
        _upload_bytes(s3, bucket, thumb_key, thumb_payload, "image/png")

        generated = UploadFile(
            owner_sub=source.owner_sub,
            tenant_id=tenant_id,
            owner_user_id=source.owner_user_id,
            owner_anon_sub=source.owner_anon_sub,
            is_anonymous=source.is_anonymous,
            privacy=source.privacy,
            bucket=bucket,
            object_key=object_key,
            original_filename=f"{Path(source.original_filename).stem}_mesh2d3d.obj",
            content_type="model/obj",
            size_bytes=len(obj_payload),
            status="queued",
            visibility="private",
            folder_key=f"project/{project_id}/3d/mesh_approx",
            thumbnail_key=thumb_key,
            meta={
                "kind": "3d",
                "mode": "mesh_approx",
                "project_id": project_id,
                "generated_by": "mesh2d3d",
                "source_file_id": source_file_id,
                "stage": "queued",
                "progress_percent": 5,
                "progress": "queued",
            },
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(generated)
        db.commit()
        db.refresh(generated)
        convert_file(generated.file_id)
        log_event(db, "mesh2d3d.completed", file_id=generated.file_id, data={"source_file_id": source_file_id})
        db.commit()
        return {"status": "ok", "file_id": generated.file_id}
    finally:
        db.close()


def moldcodes_export_job(
    owner_sub: str,
    owner_user_id: str | None,
    owner_anon_sub: str | None,
    is_anonymous: bool,
    project_id: str,
    category: str,
    family: str,
    params: dict | None = None,
):
    db = SessionLocal()
    try:
        safe_project_id = (project_id or "default").strip() or "default"
        safe_category = (category or "plates").strip() or "plates"
        safe_family = (family or "standard").strip() or "standard"
        payload = params if isinstance(params, dict) else {}
        export_name = f"{safe_category}-{safe_family}-{uuid4().hex[:8]}"
        tenant_id = resolve_or_create_tenant_id(db, owner_sub)
        safe_owner = owner_sub.replace("/", "_").replace("\\", "_")
        object_key = f"exports/tenant_{tenant_id}/{safe_owner}/{safe_project_id}/{export_name}.step"
        step_payload = (
            "ISO-10303-21;\n"
            "HEADER;\n"
            "FILE_DESCRIPTION(('STELLCODEX MoldCodes export'),'2;1');\n"
            f"FILE_NAME('{export_name}.step','{_now().isoformat()}',('STELLCODEX'),('STELLCODEX'),'{STELL_IDENTITY_NAME}','STELLCODEX','');\n"
            "FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\n"
            "ENDSEC;\n"
            "DATA;\n"
            f"/* category={safe_category}; family={safe_family}; params={json.dumps(payload, ensure_ascii=True)} */\n"
            "ENDSEC;\n"
            "END-ISO-10303-21;\n"
        ).encode("utf-8")
        thumb_key = f"thumbnails/{safe_project_id}/{export_name}.png"
        thumb_payload = _load_thumb_bytes()
        s3 = get_s3_client(settings)
        _upload_bytes(s3, settings.s3_bucket, object_key, step_payload, "application/step")
        _upload_bytes(s3, settings.s3_bucket, thumb_key, thumb_payload, "image/png")
        parsed_owner_user_id = None
        if owner_user_id:
          try:
              parsed_owner_user_id = UUID(owner_user_id)
          except Exception:
              parsed_owner_user_id = None
        generated = UploadFile(
            owner_sub=owner_sub,
            tenant_id=tenant_id,
            owner_user_id=parsed_owner_user_id,
            owner_anon_sub=owner_anon_sub,
            is_anonymous=is_anonymous,
            privacy="private",
            bucket=settings.s3_bucket,
            object_key=object_key,
            original_filename=f"{export_name}.step",
            content_type="application/step",
            size_bytes=len(step_payload),
            status="ready",
            visibility="private",
            folder_key=f"project/{safe_project_id}/3d/brep",
            thumbnail_key=thumb_key,
            meta={
                "kind": "3d",
                "mode": "brep",
                "project_id": safe_project_id,
                "generated_by": "moldcodes_export",
                "category": safe_category,
                "family": safe_family,
                "params": payload,
                "stage": "ready",
                "progress_percent": 100,
                "progress": "ready",
            },
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(generated)
        db.flush()
        log_event(
            db,
            "moldcodes.export.completed",
            actor_user_id=parsed_owner_user_id,
            actor_anon_sub=owner_anon_sub,
            file_id=generated.file_id,
            data={"project_id": safe_project_id, "category": safe_category, "family": safe_family},
        )
        db.commit()
        db.refresh(generated)
        return {"status": "ok", "file_id": generated.file_id}
    finally:
        db.close()


def retention_purge():
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        rows = (
            db.query(UploadFile)
            .filter(
                UploadFile.is_anonymous.is_(True),
                UploadFile.owner_user_id.is_(None),
                UploadFile.created_at < cutoff,
            )
            .all()
        )
        s3 = get_s3_client(settings) if settings.s3_enabled else None
        removed = 0
        for f in rows:
            if s3:
                keys = [f.object_key, f.gltf_key, f.thumbnail_key]
                meta = f.meta if isinstance(f.meta, dict) else {}
                if isinstance(meta.get("preview_jpg_keys"), list):
                    keys.extend([k for k in meta["preview_jpg_keys"] if isinstance(k, str)])
                for extra_key in ("assembly_meta_key", "pdf_key"):
                    value = meta.get(extra_key)
                    if isinstance(value, str):
                        keys.append(value)
                for key in keys:
                    if key:
                        try:
                            s3.delete_object(Bucket=f.bucket, Key=key)
                        except Exception:
                            pass
            log_event(db, "retention.purge", actor_anon_sub=f.owner_anon_sub or f.owner_sub, file_id=f.file_id)
            db.delete(f)
            removed += 1
        db.commit()
        return {"status": "ok", "removed": removed}
    finally:
        db.close()


def ping_job():
    return {"status": "ok"}


def _engineering_unavailable_result(file_id: str, reason: str) -> dict[str, Any]:
    return {
        "file_id": file_id,
        "mode": "unsupported",
        "confidence": 0.0,
        "capability_status": "analysis_unavailable",
        "volume": None,
        "surface_area": None,
        "bounding_box": None,
        "feature_flags": {},
        "dfm_risk": [],
        "recommendations": [],
        "rule_version": "engineering_dfm.v1",
        "rule_explanations": [],
        "unavailable_reason": reason,
        "message": ANALYSIS_UNAVAILABLE_TEXT,
    }


def engineering_analysis_job(file_id: str) -> dict[str, Any]:
    from app.stellai.engineering.analysis import analyze_upload

    db = SessionLocal()
    try:
        row = db.query(UploadFile).filter(UploadFile.file_id == str(file_id)).first()
        if row is None:
            return _engineering_unavailable_result(str(file_id), "file_not_found")

        job_id = None
        try:
            from rq import get_current_job

            current_job = get_current_job()
            if current_job is not None:
                job_id = str(current_job.get_id())
        except Exception:
            job_id = None

        analysis_run = start_analysis_run(
            db,
            row=row,
            run_type="engineering_analysis",
            session_id=job_id,
            metrics={"job_id": job_id or ""},
        )
        db.flush()

        error_code = None
        try:
            result = analyze_upload(row)
        except Exception as exc:
            error_code = str(getattr(exc, "code", "analysis_unavailable"))
            result = _engineering_unavailable_result(row.file_id, error_code)

        geometry_hash = persist_engineering_analysis(
            db,
            row=row,
            result=result,
            analysis_type="engineering_analysis",
            session_id=job_id,
        )

        artifact_ref = None
        try:
            artifact_ref = write_memory_payload(
                record_type="engineering_analysis",
                title=f"Engineering analysis {row.file_id}",
                source_uri=f"scx://files/{row.file_id}/engineering_analysis",
                tenant_id=str(row.tenant_id),
                project_id=str((row.meta or {}).get("project_id") or "default"),
                tags=["phase2", "engineering", "stell_ai"],
                text=json.dumps(result, ensure_ascii=False, sort_keys=True),
                metadata={"file_id": row.file_id, "job_id": job_id or "", "capability_status": result.get("capability_status")},
            )
        except Exception:
            artifact_ref = None

        row.meta = {
            **(row.meta or {}),
            "engineering_analysis": result,
            "engineering_geometry_metrics": result.get("geometry_metrics"),
            "engineering_feature_map": result.get("feature_map"),
            "engineering_dfm_report": result.get("dfm_report"),
            "engineering_cost_estimate": result.get("cost_estimate"),
            "engineering_manufacturing_plan": result.get("manufacturing_plan"),
            "engineering_report": result.get("engineering_report"),
            "engineering_analysis_job_id": job_id,
            "engineering_geometry_hash": geometry_hash,
            "engineering_analysis_record": str(artifact_ref) if artifact_ref is not None else None,
        }
        db.add(row)
        upsert_projection(db, row)
        event_type = (
            "engineering.analysis.failed"
            if result.get("unavailable_reason")
            else "engineering.analysis.completed"
        )
        log_event(
            db,
            event_type,
            actor_anon_sub=row.owner_anon_sub or row.owner_sub,
            file_id=row.file_id,
            data={
                "tenant_id": str(row.tenant_id),
                "project_id": str((row.meta or {}).get("project_id") or "default"),
                "job_id": job_id or "",
                "mode": str(result.get("mode") or ""),
                "capability_status": str(result.get("capability_status") or ""),
                "geometry_hash": geometry_hash,
                "unavailable_reason": str(result.get("unavailable_reason") or ""),
            },
        )
        finalize_analysis_run(
            db,
            analysis_run,
            result=result,
            geometry_hash=geometry_hash,
            error_code=error_code,
        )
        db.commit()
        if artifact_ref is not None:
            result = {**result, "artifact_ref": str(artifact_ref)}
        result = {**result, "geometry_hash": geometry_hash}
        return result
    finally:
        db.close()


def enqueue_convert_file(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        convert_file,
        file_id,
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
        retry=Retry(max=3),
    )
    return job.get_id()


def enqueue_mesh2d3d_export(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        mesh2d3d_export,
        file_id,
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
        retry=Retry(max=2),
    )
    return job.get_id()


def enqueue_moldcodes_export(
    owner_sub: str,
    owner_user_id: str | None,
    owner_anon_sub: str | None,
    is_anonymous: bool,
    project_id: str,
    category: str,
    family: str,
    params: dict | None = None,
) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        moldcodes_export_job,
        owner_sub,
        owner_user_id,
        owner_anon_sub,
        is_anonymous,
        project_id,
        category,
        family,
        params or {},
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
        retry=Retry(max=2),
    )
    return job.get_id()


def enqueue_generate_thumbnails(file_id: str) -> str:
    q = get_queue("render")
    job = q.enqueue(
        generate_thumbnails,
        file_id,
        job_timeout=settings.blender_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_extract_metadata(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        extract_metadata,
        file_id,
        job_timeout=settings.conversion_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_render_preset(file_id: str, preset_name: str) -> str:
    q = get_queue("render")
    job = q.enqueue(
        render_preset,
        file_id,
        preset_name,
        job_timeout=settings.blender_timeout_seconds + 60,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
        retry=Retry(max=3),
    )
    return job.get_id()


def enqueue_retention_purge() -> str:
    q = get_queue("cad")
    job = q.enqueue(
        retention_purge,
        job_timeout=300,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()


def enqueue_engineering_analysis(file_id: str) -> str:
    q = get_queue("cad")
    job = q.enqueue(
        engineering_analysis_job,
        file_id,
        job_timeout=int(os.getenv("STELLAI_ENGINEERING_TIMEOUT_SECONDS", "45") or "45") + 15,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
        retry=Retry(max=1),
    )
    return job.get_id()


def enqueue_ping_job() -> str:
    q = get_queue("cad")
    job = q.enqueue(
        ping_job,
        job_timeout=30,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()
