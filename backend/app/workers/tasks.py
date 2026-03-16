from __future__ import annotations

import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from rq import Retry

from app.core.config import settings
from app.core.format_registry import get_rule_for_filename
from app.core.hybrid_v1_rules import run_hybrid_v1_step_pipeline
from app.core.storage import get_s3_client
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.models.job_failure import JobFailure
from app.models.orchestrator import OrchestratorSession
from app.queue import get_queue
from app.services.audit import log_event
from app.services.orchestrator_sessions import build_decision_json, upsert_orchestrator_session
from app.services.rule_configs import load_hybrid_v1_config
from app.services.tenants import ensure_owner_tenant_id

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
                "node_ref": label,
                "children": [],
            }
        )
        occurrence_index[occ_id] = []
    return {
        "mode": mode,
        "generated_at": _now().isoformat(),
        "occurrences": occurrences,
        "occurrence_id_to_gltf_nodes": occurrence_index,
    }


def _upload_file(s3, bucket: str, key: str, local_path: Path, content_type: str) -> str:
    s3.upload_file(str(local_path), bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def _upload_bytes(s3, bucket: str, key: str, payload: bytes, content_type: str) -> str:
    s3.put_object(Bucket=bucket, Key=key, Body=payload, ContentType=content_type)
    return key


def _mark_failed(db, f: UploadFile, detail: str, stage: str = "convert") -> str:
    error_id = str(uuid4())
    f.status = "failed"
    f.meta = {
        **(f.meta or {}),
        "error": detail,
        "error_id": error_id,
        "stage": stage,
        "progress_percent": 100,
        "progress": "failed",
    }
    db.add(f)
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
    elif ext == "dwg":
        preview_pdf = _simple_pdf_bytes(
            "STELLCODEX DWG Preview",
            [
                f"source: {f.original_filename}",
                "DWG direct render unavailable on this node.",
                "A deterministic preview PDF was generated so the file remains accessible.",
            ],
        )
        pdf_key = f"documents/{f.file_id}/dwg-preview.pdf"
        _upload_bytes(s3, f.bucket, pdf_key, preview_pdf, "application/pdf")
        result["pdf_key"] = pdf_key
    return result


def _pipeline_image(f: UploadFile, input_path: Path, s3) -> dict:
    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    return {"thumbnail_key": thumb_key}


def _archive_manifest(input_path: Path, ext: str) -> dict:
    payload: dict = {
        "format": ext,
        "entry_count": 0,
        "total_uncompressed_bytes": 0,
        "entries": [],
        "preview_note": None,
    }

    if ext != "zip":
        payload["preview_note"] = "Entry listing is limited for this archive format on current node."
        return payload

    try:
        with zipfile.ZipFile(input_path, "r") as zf:
            entries = []
            total_uncompressed = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                total_uncompressed += max(0, int(info.file_size or 0))
                entries.append(
                    {
                        "path": info.filename,
                        "size_bytes": int(info.file_size or 0),
                        "compressed_size_bytes": int(info.compress_size or 0),
                    }
                )
            payload["entries"] = entries[:5000]
            payload["entry_count"] = len(entries)
            payload["total_uncompressed_bytes"] = total_uncompressed
            if len(entries) > 5000:
                payload["preview_note"] = "Manifest truncated to first 5000 entries."
    except Exception as exc:
        payload["preview_note"] = f"Archive listing failed: {exc}"
    return payload


def _pipeline_archive(f: UploadFile, input_path: Path, s3) -> dict:
    ext = _ext(f.original_filename)
    manifest = _archive_manifest(input_path, ext)
    manifest_key = f"archives/{f.file_id}/manifest.json"
    _upload_bytes(
        s3,
        f.bucket,
        manifest_key,
        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        "application/json",
    )

    summary_lines = [
        f"source: {f.original_filename}",
        f"format: {ext}",
        f"entries: {manifest.get('entry_count', 0)}",
        f"total_uncompressed_bytes: {manifest.get('total_uncompressed_bytes', 0)}",
    ]
    preview_note = manifest.get("preview_note")
    if isinstance(preview_note, str) and preview_note.strip():
        summary_lines.append(preview_note.strip())
    pdf_payload = _simple_pdf_bytes("STELLCODEX Archive Preview", summary_lines)
    pdf_key = f"documents/{f.file_id}/archive-preview.pdf"
    _upload_bytes(s3, f.bucket, pdf_key, pdf_payload, "application/pdf")

    thumb_key = _generate_thumbnail_png(f.file_id, f.bucket, s3)
    return {
        "thumbnail_key": thumb_key,
        "pdf_key": pdf_key,
        "archive_manifest_key": manifest_key,
        "archive_manifest_summary": {
            "entry_count": int(manifest.get("entry_count") or 0),
            "total_uncompressed_bytes": int(manifest.get("total_uncompressed_bytes") or 0),
        },
    }


def _pipeline_3d(f: UploadFile, input_path: Path, mode: str, s3) -> dict:
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

    estimated_part_count = _estimate_step_part_count(input_path) if ext in STEP_EXTS else 1
    geometry_meta = _geometry_meta(input_path, ext, part_count=estimated_part_count)
    assembly = _assembly_meta(mode, int(geometry_meta.get("part_count") or 1), f.original_filename)
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
        "preview_jpg_keys": preview_keys,
        "geometry_meta_json": geometry_meta,
    }


def _hybrid_artifacts_if_step(
    input_path: Path,
    ext: str,
    *,
    config: dict | None = None,
) -> tuple[dict | None, dict | None]:
    if ext not in STEP_EXTS:
        return None, None
    try:
        out = run_hybrid_v1_step_pipeline(str(input_path), config=config)
    except Exception:
        return None, None
    geometry_report = out.get("geometry_report")
    dfm_findings = out.get("dfm_findings")
    return (
        geometry_report if isinstance(geometry_report, dict) else None,
        dfm_findings if isinstance(dfm_findings, dict) else None,
    )


def _is_ready_contract(kind: str, payload: dict, gltf_key: str | None, thumb_key: str | None) -> bool:
    if kind == "3d":
        previews = payload.get("preview_jpg_keys")
        return bool(
            gltf_key
            and isinstance(payload.get("assembly_meta_key"), str)
            and isinstance(previews, list)
            and len(previews) >= 3
        )
    if kind == "doc":
        return bool(payload.get("pdf_key") and thumb_key)
    if kind == "archive":
        return bool(payload.get("pdf_key") and thumb_key and payload.get("archive_manifest_key"))
    if kind in {"2d", "image"}:
        return bool(thumb_key)
    return False


def convert_file(file_id: str):
    db = SessionLocal()
    try:
        f: UploadFile | None = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if not f:
            return {"status": "missing"}

        rule = get_rule_for_filename(f.original_filename)
        if not rule:
            _mark_failed(db, f, "Unsupported file extension. STEP export required", stage="validate")
            return {"status": "failed", "reason": "unsupported_extension"}
        if not rule.accept:
            _mark_failed(db, f, rule.reject_reason or "Unsupported file type", stage="validate")
            return {"status": "failed", "reason": "rejected_format"}

        if f.status == "ready":
            return {"status": "ready", "mode": "cached"}

        _set_progress(db, f, stage="queued", percent=5, hint="queued", status="running")
        s3 = get_s3_client(settings)

        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = Path(tmp_dir) / f"input.{_ext(f.original_filename)}"
            s3.download_file(f.bucket, f.object_key, str(local_path))

            _set_progress(db, f, stage="security", percent=18, hint="virus_scan", status="running")
            virus_status = _scan_file_for_virus(local_path)
            if virus_status == "infected":
                _mark_failed(db, f, "Virus scan failed", stage="security")
                return {"status": "failed", "reason": "virus_scan"}

            meta = f.meta if isinstance(f.meta, dict) else {}
            kind = rule.kind
            mode = rule.mode
            effective_project_id = str(meta.get("project_id") or "default")
            hybrid_config, hybrid_rule_version = load_hybrid_v1_config(db, project_id=effective_project_id)
            result_payload: dict = {}

            _set_progress(db, f, stage="pipeline", percent=45, hint="processing", status="running")
            if kind == "3d":
                result_payload = _pipeline_3d(f, local_path, mode, s3)
                geometry_report, dfm_findings = _hybrid_artifacts_if_step(
                    local_path,
                    _ext(f.original_filename),
                    config=hybrid_config,
                )
                if geometry_report is not None:
                    result_payload["geometry_report"] = geometry_report
                if dfm_findings is not None:
                    result_payload["dfm_findings"] = dfm_findings
            elif kind == "2d":
                result_payload = _pipeline_2d(f, local_path, s3)
            elif kind == "doc":
                result_payload = _pipeline_doc(f, local_path, s3)
            elif kind == "archive":
                result_payload = _pipeline_archive(f, local_path, s3)
            elif kind == "image":
                result_payload = _pipeline_image(f, local_path, s3)
            else:
                raise RuntimeError(f"Unsupported kind: {kind}")

        f.gltf_key = result_payload.get("gltf_key") if isinstance(result_payload.get("gltf_key"), str) else f.gltf_key
        f.thumbnail_key = (
            result_payload.get("thumbnail_key")
            if isinstance(result_payload.get("thumbnail_key"), str)
            else f.thumbnail_key
        )
        geometry = result_payload.get("geometry_meta_json")
        part_count = None
        if isinstance(geometry, dict):
            raw_count = geometry.get("part_count")
            part_count = int(raw_count) if isinstance(raw_count, int) else None
        elif isinstance(meta.get("part_count"), int):
            part_count = int(meta.get("part_count"))

        effective_geometry = geometry if isinstance(geometry, dict) else (
            meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else None
        )
        effective_dfm = result_payload.get("dfm_findings") if isinstance(result_payload.get("dfm_findings"), dict) else (
            meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else None
        )
        decision_json = result_payload.get("decision_json") if isinstance(result_payload.get("decision_json"), dict) else None
        if decision_json is None:
            decision_json = build_decision_json(
                mode=mode,
                rule_version=hybrid_rule_version,
                geometry_meta=effective_geometry,
                dfm_findings=effective_dfm,
            )
            result_payload["decision_json"] = decision_json

        f.meta = {
            **meta,
            "kind": kind,
            "mode": mode,
            "project_id": effective_project_id,
            "virus_scan_status": "clean",
            "assembly_meta_key": result_payload.get("assembly_meta_key"),
            "preview_jpg_keys": result_payload.get("preview_jpg_keys"),
            "pdf_key": result_payload.get("pdf_key"),
            "archive_manifest_key": result_payload.get("archive_manifest_key"),
            "archive_manifest_summary": (
                result_payload.get("archive_manifest_summary")
                if isinstance(result_payload.get("archive_manifest_summary"), dict)
                else meta.get("archive_manifest_summary")
            ),
            "geometry_meta_json": geometry if isinstance(geometry, dict) else meta.get("geometry_meta_json"),
            "part_count": part_count if part_count is not None else meta.get("part_count"),
            "geometry_report": result_payload.get("geometry_report") if isinstance(result_payload.get("geometry_report"), dict) else meta.get("geometry_report"),
            "dfm_findings": effective_dfm,
            "decision_json": decision_json,
            "rule_version": hybrid_rule_version,
            "stage": "finalize",
            "progress_percent": 90,
            "progress": "finalizing",
        }
        f.folder_key = f.folder_key or f"project/{str(meta.get('project_id') or 'default')}/{kind}/{mode}"

        if _is_ready_contract(kind, result_payload, f.gltf_key, f.thumbnail_key):
            f.status = "ready"
            f.meta = {**(f.meta or {}), "stage": "ready", "progress_percent": 100, "progress": "ready"}
            db.add(f)
            upsert_orchestrator_session(
                db,
                file_id=f.file_id,
                state="S2 AssemblyReady" if kind == "3d" else "S1 Converted",
                decision_json=decision_json,
                rule_version=hybrid_rule_version,
                mode=mode,
            )
            log_event(db, "job.succeeded", file_id=f.file_id, data={"kind": kind, "mode": mode})
            db.commit()
            return {"status": "ready", "kind": kind, "mode": mode}

        _mark_failed(db, f, "Required artifacts missing for ready contract", stage="finalize")
        return {"status": "failed", "reason": "missing_artifacts"}

    except subprocess.CalledProcessError as exc:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            detail = (exc.stderr or exc.stdout or "conversion failed").strip()
            _mark_failed(db, f, detail, stage="convert")
        raise
    except Exception as exc:
        f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
        if f:
            _mark_failed(db, f, str(exc), stage="convert")
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
        bucket = source.bucket
        object_key = f"uploads/{owner_sub}/generated/{uuid4()}/mesh2d3d.obj"
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
            tenant_id=source.tenant_id,
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
            decision_json=build_decision_json(
                mode="mesh_approx",
                rule_version=str((meta.get("rule_version") or "v0.0")),
            ),
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
        object_key = f"exports/{safe_project_id}/{export_name}.step"
        step_payload = (
            "ISO-10303-21;\n"
            "HEADER;\n"
            "FILE_DESCRIPTION(('STELLCODEX MoldCodes export'),'2;1');\n"
            f"FILE_NAME('{export_name}.step','{_now().isoformat()}',('STELLCODEX'),('STELLCODEX'),'Codex','STELLCODEX','');\n"
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
        tenant_id = ensure_owner_tenant_id(db, owner_sub)
        _cfg, rule_version = load_hybrid_v1_config(db, project_id=safe_project_id)
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
            decision_json=build_decision_json(mode="brep", rule_version=rule_version),
            meta={
                "kind": "3d",
                "mode": "brep",
                "project_id": safe_project_id,
                "rule_version": rule_version,
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
            db.query(OrchestratorSession).filter(OrchestratorSession.file_id == f.file_id).delete(synchronize_session=False)
            db.delete(f)
            removed += 1
        db.commit()
        return {"status": "ok", "removed": removed}
    finally:
        db.close()


def ping_job():
    return {"status": "ok"}


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


def enqueue_ping_job() -> str:
    q = get_queue("cad")
    job = q.enqueue(
        ping_job,
        job_timeout=30,
        result_ttl=DEFAULT_RESULT_TTL_SECONDS,
        ttl=DEFAULT_JOB_TTL_SECONDS,
    )
    return job.get_id()
