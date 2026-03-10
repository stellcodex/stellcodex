from __future__ import annotations

import hashlib
import math
import re
import zlib
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

try:
    import trimesh
except Exception:  # pragma: no cover - import availability is verified in tests/runtime
    trimesh = None

from app.core.format_registry import (
    extension_from_filename,
    get_rule_for_filename,
    infer_mime_from_bytes,
    match_content_type,
)
from app.services.dxf import load_doc, manifest_from_doc
from app.services.step_extractor import extract_step_geometry

FORMAT_RULE_VERSION = "format_intelligence.v1"
MAX_TEXT_CHARS = 20_000
TEXT_PREVIEW_CHARS = 480
PDF_PARSE_LIMIT_BYTES = 20 * 1024 * 1024

MATERIAL_RE = re.compile(
    r"\b(?:stainless steel|carbon steel|steel|aluminum|aluminium|brass|copper|"
    r"titanium|pla|abs|nylon|polycarbonate|pc|delrin|pom|petg|al\d{3,4}|"
    r"6061|7075)\b",
    re.IGNORECASE,
)
TOLERANCE_RE = re.compile(r"(?:±\s*\d+(?:\.\d+)?|\btol(?:erance)?\b[^\n]{0,24})", re.IGNORECASE)
PROCESS_RE = re.compile(
    r"\b(?:cnc|machining|laser cut|waterjet|weld(?:ing)?|bend(?:ing)?|"
    r"injection(?:\s*mold(?:ing)?)?|casting|sheet metal|3d print(?:ing)?|additive)\b",
    re.IGNORECASE,
)
REVISION_RE = re.compile(r"\brev(?:ision)?\s*[:.\-]?\s*[A-Z0-9]+\b", re.IGNORECASE)
UNITS_RE = re.compile(r"\b(?:mm|millimeters?|cm|centimeters?|m|meters?|inch|inches|in)\b", re.IGNORECASE)
DIMENSION_TEXT_RE = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*(?:mm|cm|m|in)\b|±\s*\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\b)",
    re.IGNORECASE,
)
OBJ_VERTEX_RE = re.compile(r"^\s*v\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+", re.MULTILINE)
OBJ_FACE_RE = re.compile(r"^\s*f\s+\S+\s+\S+\s+\S+", re.MULTILINE)
PDF_STREAM_RE = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
PDF_LITERAL_RE = re.compile(r"\((?:\\.|[^\\)])*\)")
PDF_PAGE_RE = re.compile(rb"/Type\s*/Page\b")

REAL_EXTRACTION_TIERS = {"metadata_extracted", "geometry_extracted", "dfm_supported"}


class FormatExtractionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = str(code or "EXTRACTION_FAILED")
        self.message = str(message or "Extraction failed")
        super().__init__(self.message)


def _read_head(path: Path, limit: int = 8192) -> bytes:
    with path.open("rb") as fh:
        return fh.read(limit)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _media_class(kind: str) -> str:
    token = str(kind or "").strip().lower()
    if token == "doc":
        return "document"
    if token in {"3d", "2d", "image"}:
        return token
    if token == "archive":
        return "archive"
    return "unknown"


def _pipeline_name(kind: str) -> str:
    token = str(kind or "").strip().lower()
    if token == "3d":
        return "cad_3d_ingest"
    if token == "2d":
        return "cad_2d_ingest"
    if token == "doc":
        return "document_ingest"
    if token == "image":
        return "image_ingest"
    return "unknown"


def _collapse_text(parts: list[str]) -> str:
    joined = "\n".join(item.strip() for item in parts if str(item).strip())
    return re.sub(r"[ \t]+", " ", joined).strip()


def _truncate(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _unique_matches(pattern: re.Pattern[str], text: str, *, limit: int = 12) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for match in pattern.findall(text):
        value = match if isinstance(match, str) else match[0]
        token = _truncate(str(value), 120)
        if not token or token.lower() in seen:
            continue
        seen.add(token.lower())
        out.append(token)
        if len(out) >= limit:
            break
    return out


def _detected_keywords(text: str) -> list[str]:
    mapping = {
        "material": MATERIAL_RE.search(text),
        "tolerance": TOLERANCE_RE.search(text),
        "process": PROCESS_RE.search(text),
        "revision": REVISION_RE.search(text),
        "units": UNITS_RE.search(text),
    }
    return [key for key, present in mapping.items() if present]


def _title_block_fields(lines: list[str]) -> dict[str, str]:
    labels = {
        "revision": ("rev", "revision"),
        "material": ("material", "matl"),
        "units": ("units",),
        "scale": ("scale",),
        "title": ("title", "drawing", "part name"),
        "part_number": ("part no", "part number", "p/n"),
    }
    fields: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lower()
        value = _truncate(right.strip(), 160)
        if not value:
            continue
        for canonical, aliases in labels.items():
            if canonical in fields:
                continue
            if any(alias in key for alias in aliases):
                fields[canonical] = value
    return fields


def _public_bbox(mins: list[float], maxs: list[float]) -> dict[str, Any]:
    dims = [round(maxs[idx] - mins[idx], 5) for idx in range(len(mins))]
    payload: dict[str, Any] = {
        "min": [round(value, 5) for value in mins],
        "max": [round(value, 5) for value in maxs],
        "size": dims,
    }
    if len(dims) >= 3:
        payload.update({"x": dims[0], "y": dims[1], "z": dims[2]})
    elif len(dims) == 2:
        payload.update({"x": dims[0], "y": dims[1]})
    return payload


def _signature_match(path: Path, ext: str, head: bytes) -> tuple[bool | None, str]:
    token = str(ext or "").lower().strip(".")
    upper_head = head.upper()
    if token in {"step", "stp"}:
        matched = b"ISO-10303-21" in upper_head[:4096]
        return matched, "step_signature" if matched else "missing_step_signature"
    if token == "pdf":
        matched = head.startswith(b"%PDF")
        return matched, "pdf_header" if matched else "missing_pdf_header"
    if token == "docx":
        if not head.startswith(b"PK\x03\x04"):
            return False, "missing_zip_header"
        try:
            with ZipFile(path) as archive:
                return archive.namelist().count("word/document.xml") == 1, "docx_zip_payload"
        except (BadZipFile, KeyError):
            return False, "invalid_docx_zip"
    if token == "dxf":
        text = head.decode("latin-1", errors="ignore").upper()
        matched = "SECTION" in text and ("ENTITIES" in text or "HEADER" in text)
        return matched, "dxf_text_header" if matched else "missing_dxf_header"
    if token == "obj":
        text = head.decode("utf-8", errors="ignore")
        matched = bool(OBJ_VERTEX_RE.search(text) or OBJ_FACE_RE.search(text))
        return matched, "obj_vertex_face_records" if matched else "missing_obj_records"
    if token == "stl":
        if head[:5].lower() == b"solid":
            return True, "ascii_stl_header"
        if path.stat().st_size >= 84:
            return True, "binary_stl_shape"
        return False, "invalid_stl_payload"
    return None, "no_strong_signature"


def classify_file(
    path: Path,
    *,
    original_filename: str,
    mime_type: str,
    sniffed_content_type: str | None = None,
) -> dict[str, Any]:
    head = _read_head(path)
    ext = extension_from_filename(original_filename)
    rule = get_rule_for_filename(original_filename)
    declared_mime = str(mime_type or "").strip().lower()
    sniffed = str(sniffed_content_type or infer_mime_from_bytes(head, original_filename) or "").strip().lower()
    if rule is None:
        raise FormatExtractionError("FORMAT_UNSUPPORTED", f"Unsupported format '.{ext or 'unknown'}'")
    if declared_mime and not match_content_type(declared_mime, ext):
        raise FormatExtractionError("FORMAT_CONFLICT", f"Declared content-type conflicts with .{ext}")
    if sniffed and sniffed != "application/octet-stream" and not match_content_type(sniffed, ext):
        raise FormatExtractionError("FORMAT_SIGNATURE_MISMATCH", f"Detected content does not match .{ext}")
    matched, reason = _signature_match(path, ext, head)
    if matched is False and rule.support_tier in REAL_EXTRACTION_TIERS:
        raise FormatExtractionError("FORMAT_SIGNATURE_MISMATCH", f"File signature does not match supported .{ext} payload")
    confidence = 1.0 if matched is True else 0.8 if matched is None else 0.65
    return {
        "source_format": ext or "unknown",
        "media_class": _media_class(rule.kind),
        "support_tier": rule.support_tier,
        "chosen_pipeline": _pipeline_name(rule.kind),
        "preview_supported": bool(rule.preview_supported),
        "metadata_extracted": bool(rule.metadata_extracted),
        "geometry_extracted": bool(rule.geometry_extracted),
        "dfm_supported": bool(rule.dfm_supported),
        "classification_confidence": round(confidence, 2),
        "classification_reason": reason,
        "declared_mime_type": declared_mime,
        "detected_mime_type": sniffed,
    }


def _base_result(
    *,
    file_id: str,
    tenant_id: int,
    original_filename: str,
    mime_type: str,
    size_bytes: int,
    checksum: str | None,
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "file_id": file_id,
        "tenant_id": int(tenant_id),
        "source_format": classification["source_format"],
        "media_class": classification["media_class"],
        "support_tier": classification["support_tier"],
        "classification_confidence": classification["classification_confidence"],
        "classification_reason": classification["classification_reason"],
        "chosen_pipeline": classification["chosen_pipeline"],
        "extraction_status": "processing",
        "extraction_stage": classification["chosen_pipeline"],
        "extraction_errors": [],
        "extraction_warnings": [],
        "mime_type": mime_type,
        "original_filename": original_filename,
        "size_bytes": int(size_bytes),
        "checksum": checksum,
        "detected_units": None,
        "preview_supported": bool(classification["preview_supported"]),
        "metadata_extracted": False,
        "geometry_extracted": False,
        "dfm_supported": bool(classification["dfm_supported"]),
        "engineering_rules": [],
    }


def _mesh_geometry_meta(payload: dict[str, Any]) -> dict[str, Any]:
    bbox = payload.get("bbox")
    bbox_size = bbox.get("size") if isinstance(bbox, dict) else None
    diagonal = None
    if isinstance(bbox_size, list) and len(bbox_size) >= 3:
        diagonal = round(math.sqrt(sum(float(value) ** 2 for value in bbox_size[:3])), 5)
    return {
        "units": payload.get("detected_units"),
        "bbox": bbox,
        "diagonal": diagonal,
        "part_count": int(payload.get("part_count") or 1),
        "triangle_count": payload.get("triangle_count"),
        "vertex_count": payload.get("vertex_count"),
        "face_count": payload.get("face_count"),
        "surface_area": payload.get("surface_area"),
        "volume": payload.get("volume"),
        "watertight": payload.get("watertight"),
    }


def _extract_mesh(path: Path, ext: str, classification: dict[str, Any]) -> dict[str, Any]:
    if trimesh is None:
        raise FormatExtractionError("DEPENDENCY_MISSING", "Mesh extraction dependency is unavailable")
    try:
        loaded = trimesh.load(str(path), file_type=ext, process=False, maintain_order=True)
    except Exception as exc:  # pragma: no cover - covered through safe error path
        raise FormatExtractionError("MESH_PARSE_FAILED", "Mesh payload could not be parsed") from exc
    if isinstance(loaded, trimesh.Scene):
        meshes = [
            geom.copy()
            for geom in loaded.geometry.values()
            if isinstance(geom, trimesh.Trimesh) and len(getattr(geom, "vertices", [])) > 0
        ]
        if not meshes:
            raise FormatExtractionError("MESH_EMPTY", "Mesh payload does not contain geometry")
        mesh = trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]
        is_assembly = len(meshes) > 1
        part_count = len(meshes)
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
        is_assembly = False
        part_count = 1
    else:
        raise FormatExtractionError("MESH_PARSE_FAILED", "Mesh payload is not a supported mesh object")
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise FormatExtractionError("MESH_EMPTY", "Mesh payload does not contain faces")

    bounds = mesh.bounds.tolist()
    bbox = _public_bbox(bounds[0], bounds[1])
    size = bbox.get("size") if isinstance(bbox, dict) else []
    min_dim = min(size) if isinstance(size, list) and size else None
    max_dim = max(size) if isinstance(size, list) and size else None
    surface_area = float(mesh.area) if math.isfinite(float(mesh.area)) else None
    volume = None
    watertight = bool(mesh.is_watertight)
    try:
        raw_volume = float(mesh.volume)
        if math.isfinite(raw_volume) and abs(raw_volume) > 0:
            volume = abs(raw_volume)
    except Exception:
        volume = None
    notes: list[str] = []
    if not watertight:
        notes.append("mesh is not watertight")
    if surface_area is None:
        notes.append("surface area unavailable")
    unique_vertices = {
        (
            round(float(vertex[0]), 9),
            round(float(vertex[1]), 9),
            round(float(vertex[2]), 9),
        )
        for vertex in mesh.vertices.tolist()
    }
    thin_wall_flags: list[str] = []
    if isinstance(min_dim, (int, float)) and min_dim > 0 and min_dim < 1.0:
        thin_wall_flags.append("min_bbox_dimension_below_1mm")

    result = {
        **classification,
        "metadata_extracted": True,
        "geometry_extracted": True,
        "preview_supported": True,
        "dfm_supported": True,
        "detected_units": "unknown",
        "is_assembly": is_assembly,
        "part_count": part_count,
        "body_count": int(getattr(mesh, "body_count", 1) or 1),
        "bbox": bbox,
        "volume": round(volume, 5) if isinstance(volume, (int, float)) else None,
        "surface_area": round(surface_area, 5) if isinstance(surface_area, (int, float)) else None,
        "watertight": watertight,
        "triangle_count": int(len(mesh.faces)),
        "vertex_count": int(len(unique_vertices)),
        "face_count": int(len(mesh.faces)),
        "hole_count_estimate": None,
        "thin_wall_flags": thin_wall_flags,
        "geometry_notes": notes,
    }
    result["geometry_meta_json"] = _mesh_geometry_meta(result)
    return result


def _extract_step(path: Path, classification: dict[str, Any]) -> dict[str, Any]:
    try:
        extracted = extract_step_geometry(path)
    except Exception as exc:
        raise FormatExtractionError("STEP_PARSE_FAILED", "STEP payload could not be parsed deterministically") from exc

    bbox = None
    if extracted.bbox is not None:
        bbox = {
            "x": round(float(extracted.bbox.x), 5),
            "y": round(float(extracted.bbox.y), 5),
            "z": round(float(extracted.bbox.z), 5),
            "size": [
                round(float(extracted.bbox.x), 5),
                round(float(extracted.bbox.y), 5),
                round(float(extracted.bbox.z), 5),
            ],
        }

    result = {
        **classification,
        "metadata_extracted": True,
        "geometry_extracted": True,
        "preview_supported": True,
        "dfm_supported": True,
        "detected_units": extracted.units,
        "is_assembly": bool(extracted.nauo_count > 0 or extracted.part_count > 1),
        "part_count": int(extracted.part_count),
        "body_count": int(extracted.solid_count),
        "bbox": bbox,
        "volume": round(float(extracted.volume_mm3), 5) if extracted.volume_mm3 is not None else None,
        "surface_area": None,
        "watertight": None,
        "triangle_count": None,
        "vertex_count": None,
        "face_count": int(extracted.complexity.face_count),
        "hole_count_estimate": len(extracted.holes),
        "thin_wall_flags": [],
        "geometry_notes": [str(item) for item in extracted.warnings + extracted.thread_hints if str(item).strip()],
        "component_names": [str(item) for item in extracted.component_names[:20]],
        "nauo_count": int(extracted.nauo_count),
        "surface_counts": extracted.surfaces.__dict__,
    }
    result["geometry_meta_json"] = {
        **extracted.to_geometry_meta(),
        "face_count": int(extracted.complexity.face_count),
        "body_count": int(extracted.solid_count),
        "hole_count_estimate": len(extracted.holes),
        "is_assembly": result["is_assembly"],
    }
    return result


def _entity_text(entity) -> str:
    etype = entity.dxftype()
    try:
        if etype == "TEXT":
            return str(entity.dxf.text or "").strip()
        if etype == "MTEXT":
            return str(entity.plain_text() or "").strip()
        if etype in {"ATTRIB", "ATTDEF"}:
            return str(entity.dxf.text or entity.dxf.tag or "").strip()
        if etype == "DIMENSION":
            return str(entity.dxf.text or "").strip()
    except Exception:
        return ""
    return ""


def _extract_dxf(path: Path, classification: dict[str, Any]) -> dict[str, Any]:
    try:
        doc = load_doc(str(path))
    except Exception as exc:
        raise FormatExtractionError("DXF_PARSE_FAILED", "DXF payload could not be parsed") from exc

    manifest = manifest_from_doc(doc)
    entity_counts = manifest.get("entity_counts") if isinstance(manifest.get("entity_counts"), dict) else {}
    lines: list[str] = []
    dimension_text: list[str] = []
    for entity in doc.modelspace():
        text = _entity_text(entity)
        if not text:
            continue
        lines.append(text)
        if DIMENSION_TEXT_RE.search(text):
            dimension_text.append(_truncate(text, 120))
    text_blob = _collapse_text(lines)
    bbox = manifest.get("bbox") if isinstance(manifest.get("bbox"), dict) else {}
    width = float(bbox.get("max_x", 0) - bbox.get("min_x", 0)) if bbox else 0.0
    height = float(bbox.get("max_y", 0) - bbox.get("min_y", 0)) if bbox else 0.0
    block_count = len([block for block in doc.blocks if not str(block.name or "").startswith("*")])
    units_name = str(((manifest.get("units") or {}).get("name")) or "unknown")
    notes = [_truncate(text, 160) for text in lines if text and text not in dimension_text][:10]

    result = {
        **classification,
        "metadata_extracted": True,
        "geometry_extracted": False,
        "preview_supported": True,
        "dfm_supported": True,
        "detected_units": units_name if units_name != "unitless" else "unknown",
        "sheet_count": 1,
        "entity_count": int(sum(int(value) for value in entity_counts.values())),
        "layer_count": int(len(manifest.get("layers") or [])),
        "block_count": int(block_count),
        "text_count": int(len(lines)),
        "dimension_text": dimension_text[:10],
        "title_block_fields": _title_block_fields(lines),
        "drawing_notes": notes,
        "units": units_name,
        "page_size": {"width": round(width, 5), "height": round(height, 5)} if width > 0 and height > 0 else None,
        "bounds": bbox or None,
        "detected_keywords": _detected_keywords(text_blob),
        "material_mentions": _unique_matches(MATERIAL_RE, text_blob),
        "tolerance_mentions": _unique_matches(TOLERANCE_RE, text_blob),
        "process_mentions": _unique_matches(PROCESS_RE, text_blob),
        "revision_mentions": _unique_matches(REVISION_RE, text_blob),
    }
    return result


def _decode_pdf_literal(raw: str) -> str:
    text = raw[1:-1]
    text = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), text)
    text = text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\n", " ").replace(r"\r", " ")
    text = text.replace(r"\t", " ").replace(r"\\", "\\")
    return _truncate(text, 400)


def _extract_pdf_text(data: bytes) -> list[str]:
    candidates: list[bytes] = [data]
    for match in PDF_STREAM_RE.finditer(data):
        header = match.group(1)
        stream = match.group(2).strip(b"\r\n")
        if b"/FlateDecode" in header:
            try:
                candidates.append(zlib.decompress(stream))
            except Exception:
                continue
        else:
            candidates.append(stream)
    lines: list[str] = []
    for chunk in candidates:
        text = chunk.decode("latin-1", errors="ignore")
        for literal in PDF_LITERAL_RE.findall(text):
            decoded = _decode_pdf_literal(literal)
            if decoded:
                lines.append(decoded)
    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped


def _extract_pdf(path: Path, classification: dict[str, Any]) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) > PDF_PARSE_LIMIT_BYTES:
        raise FormatExtractionError("PDF_TOO_LARGE", "PDF text extraction limit exceeded")
    if not data.startswith(b"%PDF"):
        raise FormatExtractionError("PDF_PARSE_FAILED", "PDF header is invalid")
    page_count = len(PDF_PAGE_RE.findall(data))
    if page_count == 0:
        page_count = 1
    lines = _extract_pdf_text(data)
    text_blob = _collapse_text(lines)[:MAX_TEXT_CHARS]
    preview = _truncate(text_blob, TEXT_PREVIEW_CHARS)
    result = {
        **classification,
        "metadata_extracted": True,
        "geometry_extracted": False,
        "preview_supported": True,
        "dfm_supported": True,
        "page_count": int(page_count),
        "extracted_text": text_blob,
        "extracted_text_preview": preview,
        "detected_keywords": _detected_keywords(text_blob),
        "material_mentions": _unique_matches(MATERIAL_RE, text_blob),
        "tolerance_mentions": _unique_matches(TOLERANCE_RE, text_blob),
        "process_mentions": _unique_matches(PROCESS_RE, text_blob),
        "revision_mentions": _unique_matches(REVISION_RE, text_blob),
        "document_notes": [_truncate(line, 160) for line in lines[:8]],
        "title_block_fields": _title_block_fields(lines),
    }
    if not text_blob:
        result.setdefault("extraction_warnings", []).append("pdf_text_not_found")
    return result


def _docx_xml_lines(path: Path) -> list[str]:
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            if "word/document.xml" not in names:
                raise FormatExtractionError("DOCX_PARSE_FAILED", "DOCX payload is missing document.xml")
            payloads = [name for name in names if name.startswith("word/") and name.endswith(".xml")]
            lines: list[str] = []
            for name in payloads:
                raw = archive.read(name)
                root = ET.fromstring(raw)
                for node in root.iter():
                    if node.tag.endswith("}t") and node.text:
                        lines.append(node.text)
            return lines
    except BadZipFile as exc:
        raise FormatExtractionError("DOCX_PARSE_FAILED", "DOCX payload is not a valid zip package") from exc


def _extract_docx(path: Path, classification: dict[str, Any]) -> dict[str, Any]:
    lines = _docx_xml_lines(path)
    text_blob = _collapse_text(lines)[:MAX_TEXT_CHARS]
    result = {
        **classification,
        "metadata_extracted": True,
        "geometry_extracted": False,
        "preview_supported": True,
        "dfm_supported": True,
        "page_count": None,
        "extracted_text": text_blob,
        "extracted_text_preview": _truncate(text_blob, TEXT_PREVIEW_CHARS),
        "detected_keywords": _detected_keywords(text_blob),
        "material_mentions": _unique_matches(MATERIAL_RE, text_blob),
        "tolerance_mentions": _unique_matches(TOLERANCE_RE, text_blob),
        "process_mentions": _unique_matches(PROCESS_RE, text_blob),
        "revision_mentions": _unique_matches(REVISION_RE, text_blob),
        "document_notes": [_truncate(line, 160) for line in lines[:8]],
        "title_block_fields": _title_block_fields(lines),
    }
    if not text_blob:
        result.setdefault("extraction_warnings", []).append("docx_text_not_found")
    return result


def _engineering_rules(result: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []

    def _emit(
        rule_id: str,
        *,
        severity: str,
        status: str,
        message: str,
        evidence: dict[str, Any],
        source_fields_used: list[str],
    ) -> None:
        rules.append(
            {
                "rule_id": rule_id,
                "rule_version": FORMAT_RULE_VERSION,
                "severity": severity,
                "status": status,
                "message": message,
                "evidence": evidence,
                "confidence": 1.0,
                "source_fields_used": source_fields_used,
            }
        )

    media_class = str(result.get("media_class") or "")
    if media_class == "3d" and result.get("geometry_extracted"):
        bbox = result.get("bbox") if isinstance(result.get("bbox"), dict) else {}
        size = bbox.get("size") if isinstance(bbox.get("size"), list) else []
        min_dim = min(size) if size else None
        max_dim = max(size) if size else None
        if result.get("watertight") is False:
            _emit(
                "mesh_not_watertight",
                severity="high",
                status="warn",
                message="Mesh is not watertight.",
                evidence={"watertight": False},
                source_fields_used=["watertight"],
            )
        if str(result.get("detected_units") or "").lower() in {"", "unknown", "unitless"}:
            _emit(
                "units_missing",
                severity="medium",
                status="warn",
                message="Units are missing or unknown.",
                evidence={"detected_units": result.get("detected_units")},
                source_fields_used=["detected_units"],
            )
        if result.get("volume") in {None, 0, 0.0}:
            _emit(
                "zero_volume_anomaly",
                severity="medium",
                status="warn",
                message="Volume is empty or could not be resolved deterministically.",
                evidence={"volume": result.get("volume")},
                source_fields_used=["volume"],
            )
        if isinstance(min_dim, (int, float)) and isinstance(max_dim, (int, float)) and min_dim > 0 and (max_dim / min_dim) >= 25:
            _emit(
                "extreme_aspect_ratio",
                severity="medium",
                status="warn",
                message="Bounding box aspect ratio is unusually high.",
                evidence={"bbox_size": size},
                source_fields_used=["bbox"],
            )
        tri_count = result.get("triangle_count")
        if isinstance(tri_count, int) and tri_count >= 250_000:
            _emit(
                "triangle_count_high",
                severity="medium",
                status="warn",
                message="Triangle count is unusually high for deterministic downstream processing.",
                evidence={"triangle_count": tri_count},
                source_fields_used=["triangle_count"],
            )
        if bool(result.get("is_assembly")) and int(result.get("part_count") or 0) <= 1:
            _emit(
                "assembly_part_mismatch",
                severity="medium",
                status="warn",
                message="Assembly classification does not match extracted part count.",
                evidence={"is_assembly": result.get("is_assembly"), "part_count": result.get("part_count")},
                source_fields_used=["is_assembly", "part_count"],
            )
        thin_flags = result.get("thin_wall_flags")
        if isinstance(thin_flags, list) and thin_flags:
            _emit(
                "thin_geometry_suspected",
                severity="medium",
                status="warn",
                message="Thin geometry was inferred from deterministic bounding dimensions.",
                evidence={"thin_wall_flags": thin_flags},
                source_fields_used=["thin_wall_flags", "bbox"],
            )
    elif media_class in {"2d", "document"} and result.get("metadata_extracted"):
        if not result.get("revision_mentions"):
            _emit(
                "revision_indicator_missing",
                severity="medium",
                status="warn",
                message="No revision indicator was detected.",
                evidence={"revision_mentions": []},
                source_fields_used=["revision_mentions"],
            )
        if not result.get("material_mentions"):
            _emit(
                "material_mention_missing",
                severity="medium",
                status="warn",
                message="No material mention was detected.",
                evidence={"material_mentions": []},
                source_fields_used=["material_mentions"],
            )
        if not result.get("tolerance_mentions"):
            _emit(
                "tolerance_mention_missing",
                severity="medium",
                status="warn",
                message="No tolerance mention was detected.",
                evidence={"tolerance_mentions": []},
                source_fields_used=["tolerance_mentions"],
            )
        units = str(result.get("units") or result.get("detected_units") or "").lower()
        if units in {"", "unknown", "unitless"}:
            _emit(
                "drawing_units_missing",
                severity="medium",
                status="warn",
                message="Units were not detected in the drawing/document metadata.",
                evidence={"units": result.get("units") or result.get("detected_units")},
                source_fields_used=["units", "detected_units"],
            )
        sparse = int(result.get("text_count") or 0) < 2 and not bool(result.get("title_block_fields"))
        if sparse and media_class == "2d":
            _emit(
                "sparse_drawing_metadata",
                severity="medium",
                status="warn",
                message="Drawing metadata is sparse for deterministic review.",
                evidence={"text_count": result.get("text_count"), "title_block_fields": result.get("title_block_fields")},
                source_fields_used=["text_count", "title_block_fields"],
            )
    return rules


def extract_format_intelligence(
    path: Path,
    *,
    file_id: str,
    tenant_id: int,
    original_filename: str,
    mime_type: str,
    size_bytes: int,
    checksum: str | None = None,
    sniffed_content_type: str | None = None,
) -> dict[str, Any]:
    checksum_value = checksum or _sha256(path)
    try:
        classification = classify_file(
            path,
            original_filename=original_filename,
            mime_type=mime_type,
            sniffed_content_type=sniffed_content_type,
        )
    except FormatExtractionError as exc:
        rule = get_rule_for_filename(original_filename)
        fallback = {
            "source_format": extension_from_filename(original_filename) or "unknown",
            "media_class": _media_class(rule.kind) if rule is not None else "unknown",
            "support_tier": rule.support_tier if rule is not None else "unsupported",
            "chosen_pipeline": _pipeline_name(rule.kind) if rule is not None else "unknown",
            "preview_supported": bool(rule.preview_supported) if rule is not None else False,
            "metadata_extracted": bool(rule.metadata_extracted) if rule is not None else False,
            "geometry_extracted": bool(rule.geometry_extracted) if rule is not None else False,
            "dfm_supported": bool(rule.dfm_supported) if rule is not None else False,
            "classification_confidence": 0.0,
            "classification_reason": "classification_failed",
            "declared_mime_type": str(mime_type or "").strip().lower(),
            "detected_mime_type": str(sniffed_content_type or "").strip().lower(),
        }
        result = _base_result(
            file_id=file_id,
            tenant_id=tenant_id,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum_value,
            classification=fallback,
        )
        result["extraction_status"] = "failed"
        result["extraction_stage"] = "failed"
        result["extraction_errors"] = [{"code": exc.code, "message": exc.message}]
        return result
    result = _base_result(
        file_id=file_id,
        tenant_id=tenant_id,
        original_filename=original_filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        checksum=checksum_value,
        classification=classification,
    )
    ext = str(classification["source_format"] or "")

    try:
        if classification["support_tier"] not in REAL_EXTRACTION_TIERS:
            result["extraction_status"] = "unsupported"
            result["extraction_stage"] = "unsupported"
            result["extraction_warnings"] = [f"format support tier is {classification['support_tier']}"]
            return result
        if ext in {"stl", "obj"}:
            extracted = _extract_mesh(path, ext, classification)
        elif ext in {"step", "stp"}:
            extracted = _extract_step(path, classification)
        elif ext == "dxf":
            extracted = _extract_dxf(path, classification)
        elif ext == "pdf":
            extracted = _extract_pdf(path, classification)
        elif ext == "docx":
            extracted = _extract_docx(path, classification)
        else:
            raise FormatExtractionError("FORMAT_UNSUPPORTED", f"No deterministic extractor is available for .{ext}")
    except FormatExtractionError as exc:
        result["extraction_status"] = "failed"
        result["extraction_stage"] = "failed"
        result["extraction_errors"] = [{"code": exc.code, "message": exc.message}]
        return result
    except Exception as exc:  # pragma: no cover - safety net
        result["extraction_status"] = "failed"
        result["extraction_stage"] = "failed"
        result["extraction_errors"] = [{"code": "EXTRACTION_FAILED", "message": "Extraction failed safely"}]
        result.setdefault("extraction_warnings", []).append(type(exc).__name__)
        return result

    result.update(extracted)
    result["engineering_rules"] = _engineering_rules(result)
    result["extraction_status"] = "completed"
    result["extraction_stage"] = "completed"
    return result


def public_extraction_summary(meta: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = meta.get("extraction_result") if isinstance(meta, dict) else None
    if not isinstance(payload, dict):
        return None
    summary: dict[str, Any] = {
        "source_format": payload.get("source_format"),
        "media_class": payload.get("media_class"),
        "support_tier": payload.get("support_tier"),
        "extraction_status": payload.get("extraction_status"),
        "extraction_stage": payload.get("extraction_stage"),
        "classification_confidence": payload.get("classification_confidence"),
        "classification_reason": payload.get("classification_reason"),
        "detected_units": payload.get("detected_units"),
        "preview_supported": bool(payload.get("preview_supported")),
        "metadata_extracted": bool(payload.get("metadata_extracted")),
        "geometry_extracted": bool(payload.get("geometry_extracted")),
        "dfm_supported": bool(payload.get("dfm_supported")),
        "errors": payload.get("extraction_errors") if isinstance(payload.get("extraction_errors"), list) else [],
        "warnings": payload.get("extraction_warnings") if isinstance(payload.get("extraction_warnings"), list) else [],
    }
    for key in (
        "is_assembly",
        "part_count",
        "body_count",
        "bbox",
        "volume",
        "surface_area",
        "watertight",
        "triangle_count",
        "vertex_count",
        "face_count",
        "hole_count_estimate",
        "thin_wall_flags",
        "geometry_notes",
        "sheet_count",
        "entity_count",
        "layer_count",
        "block_count",
        "text_count",
        "dimension_text",
        "title_block_fields",
        "drawing_notes",
        "units",
        "page_size",
        "bounds",
        "page_count",
        "detected_keywords",
        "material_mentions",
        "tolerance_mentions",
        "process_mentions",
        "revision_mentions",
        "document_notes",
    ):
        value = payload.get(key)
        if value not in (None, [], {}, ""):
            summary[key] = value
    preview = payload.get("extracted_text_preview")
    if isinstance(preview, str) and preview:
        summary["extracted_text_preview"] = _truncate(preview, TEXT_PREVIEW_CHARS)
    rules = payload.get("engineering_rules")
    if isinstance(rules, list) and rules:
        summary["engineering_rules"] = [rule for rule in rules[:10] if isinstance(rule, dict)]
    return summary
