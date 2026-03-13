from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import trimesh
except Exception:  # pragma: no cover - fallback path
    trimesh = None

try:
    import pyvista
except Exception:  # pragma: no cover - fallback path
    pyvista = None

from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution

_ALLOWED_EXT = {".stl", ".obj", ".ply"}


def build_cad_tools(*, security_policy: ToolSecurityPolicy | None) -> list[ToolDefinition]:
    policy = security_policy or ToolSecurityPolicy()
    return [
        ToolDefinition(
            name="mesh_info",
            description="Return mesh metadata for STL/OBJ/PLY files in tenant-safe storage.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            output_schema={"type": "object"},
            permission_scope="stellai.cad.read",
            tenant_required=True,
            handler=_build_mesh_info_handler(policy),
            category="cad",
            tags=("geometry",),
        ),
        ToolDefinition(
            name="mesh_volume",
            description="Compute mesh volume for STL/OBJ/PLY files.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            output_schema={"type": "object"},
            permission_scope="stellai.cad.read",
            tenant_required=True,
            handler=_build_mesh_volume_handler(policy),
            category="cad",
            tags=("geometry",),
        ),
        ToolDefinition(
            name="mesh_surface_area",
            description="Compute mesh surface area for STL/OBJ/PLY files.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            output_schema={"type": "object"},
            permission_scope="stellai.cad.read",
            tenant_required=True,
            handler=_build_mesh_surface_area_handler(policy),
            category="cad",
            tags=("geometry",),
        ),
        ToolDefinition(
            name="mesh_bounds",
            description="Compute axis-aligned bounds for STL/OBJ/PLY files.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            output_schema={"type": "object"},
            permission_scope="stellai.cad.read",
            tenant_required=True,
            handler=_build_mesh_bounds_handler(policy),
            category="cad",
            tags=("geometry",),
        ),
    ]


def _build_mesh_info_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        loaded = _load_mesh(policy=policy, context=context, params=params, tool_name="mesh_info")
        if isinstance(loaded, ToolExecution):
            return loaded
        mesh, path = loaded
        bounds = mesh.bounds.tolist() if getattr(mesh, "bounds", None) is not None else None
        return ToolExecution(
            tool_name="mesh_info",
            status="ok",
            output={
                "resource": path.name,
                "format": path.suffix.lower().lstrip("."),
                "vertex_count": int(len(mesh.vertices)),
                "face_count": int(len(mesh.faces)),
                "is_watertight": bool(mesh.is_watertight),
                "is_volume": bool(mesh.is_volume),
                "bounds": bounds,
                "extents": mesh.extents.tolist() if getattr(mesh, "extents", None) is not None else None,
                "backend": "trimesh",
                "pyvista_available": pyvista is not None,
            },
        )

    return _handler


def _build_mesh_volume_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        loaded = _load_mesh(policy=policy, context=context, params=params, tool_name="mesh_volume")
        if isinstance(loaded, ToolExecution):
            return loaded
        mesh, path = loaded
        return ToolExecution(
            tool_name="mesh_volume",
            status="ok",
            output={
                "resource": path.name,
                "volume": float(mesh.volume),
                "is_watertight": bool(mesh.is_watertight),
            },
        )

    return _handler


def _build_mesh_surface_area_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        loaded = _load_mesh(policy=policy, context=context, params=params, tool_name="mesh_surface_area")
        if isinstance(loaded, ToolExecution):
            return loaded
        mesh, path = loaded
        return ToolExecution(
            tool_name="mesh_surface_area",
            status="ok",
            output={"resource": path.name, "surface_area": float(mesh.area)},
        )

    return _handler


def _build_mesh_bounds_handler(policy: ToolSecurityPolicy):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        loaded = _load_mesh(policy=policy, context=context, params=params, tool_name="mesh_bounds")
        if isinstance(loaded, ToolExecution):
            return loaded
        mesh, path = loaded
        bounds = mesh.bounds
        return ToolExecution(
            tool_name="mesh_bounds",
            status="ok",
            output={
                "resource": path.name,
                "min": bounds[0].tolist(),
                "max": bounds[1].tolist(),
                "extents": mesh.extents.tolist(),
            },
        )

    return _handler


def _load_mesh(
    *,
    policy: ToolSecurityPolicy,
    context: RuntimeContext,
    params: dict[str, Any],
    tool_name: str,
):
    if trimesh is None:
        return ToolExecution(
            tool_name=tool_name,
            status="failed",
            reason="dependency_missing",
            output={"error": {"reason": "dependency_missing", "missing": ["trimesh"]}},
        )

    raw_path = str(params.get("path") or "")
    if not raw_path:
        return ToolExecution(
            tool_name=tool_name,
            status="denied",
            reason="missing_path",
            output={"error": {"reason": "missing_path"}},
        )

    validated = policy.validate_path(context=context, raw_path=raw_path, must_exist=True, expect_directory=False)
    if not validated.allowed or validated.path is None:
        return ToolExecution(
            tool_name=tool_name,
            status="denied",
            reason=validated.reason,
            output={"error": {"reason": validated.reason}},
        )

    path = validated.path
    if path.suffix.lower() not in _ALLOWED_EXT:
        return ToolExecution(
            tool_name=tool_name,
            status="denied",
            reason="unsupported_mesh_format",
            output={"error": {"reason": "unsupported_mesh_format", "allowed": sorted(_ALLOWED_EXT)}},
        )

    try:
        loaded = trimesh.load(path, force="mesh", process=False, skip_materials=True)
        if isinstance(loaded, trimesh.Scene):
            geometries = [geom for geom in loaded.geometry.values() if isinstance(geom, trimesh.Trimesh)]
            if not geometries:
                raise ValueError("empty_scene")
            loaded = trimesh.util.concatenate(geometries)
        if not isinstance(loaded, trimesh.Trimesh):
            raise TypeError("mesh_unavailable")
        return loaded, path
    except Exception:
        return ToolExecution(
            tool_name=tool_name,
            status="failed",
            reason="geometry_error",
            output={"error": {"reason": "geometry_error"}},
        )
