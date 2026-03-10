from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def library_status() -> dict[str, bool]:
    return {
        "trimesh": _module_available("trimesh"),
        "open3d": _module_available("open3d"),
        "numpy": _module_available("numpy"),
        "scipy": _module_available("scipy"),
        "shapely": _module_available("shapely"),
        "networkx": _module_available("networkx"),
        "meshio": _module_available("meshio"),
        "pyvista": _module_available("pyvista"),
        "cadquery": _module_available("cadquery"),
        "ocp": _module_available("OCP"),
        "pythonocc_core": _module_available("OCC"),
    }


def occ_available() -> bool:
    status = library_status()
    return bool(status.get("cadquery") and status.get("ocp"))


def _capability_row(
    *,
    ext: str,
    mode: str,
    capability_status: str,
    confidence: float,
    unavailable_reason: str | None = None,
) -> dict[str, Any]:
    row = {
        "ext": ext,
        "mode": mode,
        "confidence": round(float(confidence), 4),
        "capability_status": capability_status,
    }
    if unavailable_reason:
        row["unavailable_reason"] = unavailable_reason
    return row


def detect_engineering_capability(filename: str, *, occ_enabled: bool | None = None) -> dict[str, Any]:
    ext = Path(filename or "").suffix.lower().lstrip(".")
    occ_enabled = occ_available() if occ_enabled is None else bool(occ_enabled)

    if ext in {"step", "stp"}:
        if occ_enabled:
            return _capability_row(ext=ext, mode="brep", capability_status="brep_ready", confidence=0.92)
        return _capability_row(
            ext=ext,
            mode="brep",
            capability_status="limited_without_occ",
            confidence=0.58,
            unavailable_reason="CadQuery + OCP tabanli B-Rep yolu kullanilamiyor; yalnizca deterministik STEP cikarimi mevcut.",
        )
    if ext in {"stl", "obj", "ply"}:
        return _capability_row(ext=ext, mode="mesh_approx", capability_status="supported", confidence=0.78)
    if ext in {"gltf", "glb"}:
        return _capability_row(
            ext=ext,
            mode="visual_only",
            capability_status="preview_only",
            confidence=0.2,
            unavailable_reason="Gorsel onizleme disinda deterministik muhendislik analizi yok.",
        )
    if ext == "dxf":
        return _capability_row(
            ext=ext,
            mode="preview_only",
            capability_status="limited_preview",
            confidence=0.32,
            unavailable_reason="DXF yolu sinirli ve onizleme odaklidir.",
        )
    if ext in {"iges", "igs"}:
        return _capability_row(
            ext=ext,
            mode="brep",
            capability_status="experimental",
            confidence=0.25,
            unavailable_reason="IGES/IGS yolu deneysel durumda.",
        )
    if ext in {"x_t", "x_b"}:
        return _capability_row(
            ext=ext,
            mode="unsupported",
            capability_status="unsupported",
            confidence=0.0,
            unavailable_reason="Parasolid yolu bu runtime tarafinda dogrulanmadi.",
        )
    return _capability_row(
        ext=ext or "unknown",
        mode="unsupported",
        capability_status="unsupported",
        confidence=0.0,
        unavailable_reason="Format bu analiz akisi tarafindan desteklenmiyor.",
    )


def engineering_support_matrix() -> dict[str, Any]:
    status = library_status()
    occ_enabled = occ_available()
    rows = [
        detect_engineering_capability("sample.step", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.stp", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.stl", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.obj", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.ply", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.gltf", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.glb", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.dxf", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.iges", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.igs", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.x_t", occ_enabled=occ_enabled),
        detect_engineering_capability("sample.x_b", occ_enabled=occ_enabled),
    ]
    return {
        "rule_version": "engineering_capability.v1",
        "libraries": status,
        "occ_enabled": occ_enabled,
        "formats": rows,
    }
