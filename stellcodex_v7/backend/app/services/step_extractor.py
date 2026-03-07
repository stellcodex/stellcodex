"""
app/services/step_extractor.py

Pure-Python STEP (ISO 10303-21, AP203/AP214) geometry extractor.

No external CAD library required — reads the STEP entity text directly.

What is extracted
-----------------
- Unit system         (from SI_UNIT / CONVERSION_BASED_UNIT in header)
- Bounding box        (from all CARTESIAN_POINT coordinates)
- Volume estimate     (bounding-box volume; overestimate, but useful for material block sizing)
- Solid / part count  (MANIFOLD_SOLID_BREP entities)
- Holes               (CIRCLE entities resolved through AXIS2_PLACEMENT_3D → radius + axis direction + depth)
- Surface breakdown   (PLANE, CYLINDRICAL_SURFACE, CONICAL_SURFACE, SPHERICAL_SURFACE, B_SPLINE_SURFACE …)
- Thread hints        (HELICOIDAL_SURFACE presence)
- Assembly names      (PRODUCT entities + NEXT_ASSEMBLY_USAGE_OCCURRENCE count)
- Complexity rating   (face count + entity count → LOW / MED / HIGH)

Integration
-----------
    from app.services.step_extractor import extract_step_geometry, geometry_meta_from_step

    # Full result object
    result = extract_step_geometry(path)

    # Dict compatible with existing geometry_meta_json field in UploadFile.meta
    meta = geometry_meta_from_step(path)

Limitations (V1)
----------------
- No true B-rep kernel: measurements come from text-level entity parsing.
- Bounding box includes ALL CARTESIAN_POINT coordinates (control points of splines
  are included), so it may be slightly larger than the true tight bounding box.
- Hole depth is computed as the projection range of circle centers along the hole axis;
  this is correct for axis-aligned cylindrical holes and approximate for angled holes.
- Thread detection relies on HELICOIDAL_SURFACE entity presence; most CAD systems
  represent threads as annotations, not geometry, so this flag may be absent even
  when threads exist.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FILE_BYTES = 200 * 1024 * 1024  # 200 MB read guard

_COMPLEXITY_LOW_MAX = 300
_COMPLEXITY_MED_MAX = 2_000

# STEP float literal: handles  1.0  1.  .5  1.5E+02  -0.  0
_FLOAT = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?"

# ---------------------------------------------------------------------------
# Compiled regex patterns
# (applied to the whitespace-collapsed DATA section for reliability)
# ---------------------------------------------------------------------------

_RE_CARTESIAN = re.compile(
    rf"#\s*(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*'[^']*'\s*,"
    rf"\s*\(\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*\)\s*\)"
)
_RE_DIRECTION = re.compile(
    rf"#\s*(\d+)\s*=\s*DIRECTION\s*\(\s*'[^']*'\s*,"
    rf"\s*\(\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*\)\s*\)"
)
_RE_CIRCLE = re.compile(
    rf"#\s*(\d+)\s*=\s*CIRCLE\s*\(\s*'[^']*'\s*,\s*#\s*(\d+)\s*,\s*({_FLOAT})\s*\)"
)
_RE_AXIS2P3D = re.compile(
    r"#\s*(\d+)\s*=\s*AXIS2_PLACEMENT_3D\s*\(\s*'[^']*'\s*,"
    r"\s*#\s*(\d+)\s*,\s*#\s*(\d+)(?:\s*,\s*#\s*(\d+))?\s*\)"
)
_RE_MANIFOLD_BREP   = re.compile(r"#\s*\d+\s*=\s*MANIFOLD_SOLID_BREP\s*\(")
_RE_PLANE           = re.compile(r"#\s*\d+\s*=\s*PLANE\s*\(")
_RE_CYLINDRICAL     = re.compile(r"#\s*\d+\s*=\s*CYLINDRICAL_SURFACE\s*\(")
_RE_CONICAL         = re.compile(r"#\s*\d+\s*=\s*CONICAL_SURFACE\s*\(")
_RE_SPHERICAL       = re.compile(r"#\s*\d+\s*=\s*SPHERICAL_SURFACE\s*\(")
_RE_TOROIDAL        = re.compile(r"#\s*\d+\s*=\s*TOROIDAL_SURFACE\s*\(")
_RE_BSPLINE         = re.compile(r"#\s*\d+\s*=\s*B_SPLINE_SURFACE")
_RE_ADVANCED_FACE   = re.compile(r"#\s*\d+\s*=\s*ADVANCED_FACE\s*\(")
_RE_HELICOIDAL      = re.compile(r"\bHELICOIDAL_SURFACE\b")
_RE_NAUO            = re.compile(r"#\s*\d+\s*=\s*NEXT_ASSEMBLY_USAGE_OCCURRENCE\s*\(")
_RE_PROD_DEF_SHAPE  = re.compile(r"#\s*\d+\s*=\s*PRODUCT_DEFINITION_SHAPE\s*\(")
_RE_PRODUCT         = re.compile(
    r"#\s*(\d+)\s*=\s*PRODUCT\s*\(\s*'([^']*)'\s*,\s*'([^']*)'"
)

# Unit detection patterns (checked against header + first 5 KB of data)
_RE_SI_MILLI_METRE  = re.compile(r"\.MILLI\.\s*[,)]\s*\.METRE\.")
_RE_SI_CENTI_METRE  = re.compile(r"\.CENTI\.\s*[,)]\s*\.METRE\.")
_RE_SI_METRE        = re.compile(r"SI_UNIT\s*\(\s*\$\s*,\s*\.METRE\.")
_RE_INCH            = re.compile(r"CONVERSION_BASED_UNIT\s*\(\s*'(?:INCH|inch)'")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BoundingBox:
    x: float        # width  (mm)
    y: float        # depth  (mm)
    z: float        # height (mm)
    diagonal: float # space diagonal (mm)


@dataclass
class HoleFeature:
    index: int
    radius_mm: float
    diameter_mm: float
    axis: list[float]           # normalised direction vector [dx, dy, dz]
    depth_mm: float | None      # None if only one circle found for this hole
    center: list[float] | None  # approximate 3D centroid of hole axis [x, y, z]


@dataclass
class SurfaceCounts:
    plane: int      = 0
    cylindrical: int = 0
    conical: int    = 0
    spherical: int  = 0
    toroidal: int   = 0
    b_spline: int   = 0
    other: int      = 0


@dataclass
class ComplexityInfo:
    entity_count: int   # rough entity count from DATA section
    face_count: int     # number of ADVANCED_FACE entities
    score: int          # weighted score
    label: str          # "LOW" | "MED" | "HIGH"


@dataclass
class StepGeometryResult:
    filename: str
    size_bytes: int
    units: str              # "mm" | "inch" | "m" | "cm" | "unknown"

    bbox: BoundingBox | None
    volume_mm3: float | None    # bounding-box overestimate in mm³

    solid_count: int
    part_count: int

    holes: list[HoleFeature]
    surfaces: SurfaceCounts

    has_threads: bool
    thread_hints: list[str]

    component_names: list[str]  # from PRODUCT entities
    nauo_count: int             # number of assembly relationships

    complexity: ComplexityInfo
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_geometry_meta(self) -> dict[str, Any]:
        """
        Returns a dict that is backward-compatible with the existing
        geometry_meta_json field structure used in tasks.py / explorer.py.
        """
        bbox_dict: dict | None = None
        diagonal: float | None = None
        if self.bbox:
            bbox_dict = {"x": self.bbox.x, "y": self.bbox.y, "z": self.bbox.z}
            diagonal = self.bbox.diagonal

        return {
            # Fields already expected by the existing pipeline
            "units": self.units,
            "bbox": bbox_dict,
            "diagonal": diagonal,
            "part_count": self.part_count,
            "volume": self.volume_mm3,
            "triangle_count": None,  # mesh triangulation not performed here
            # Extended fields (ignored by existing code, available for future use)
            "holes": [asdict(h) for h in self.holes],
            "surfaces": asdict(self.surfaces),
            "has_threads": self.has_threads,
            "thread_hints": self.thread_hints,
            "component_names": self.component_names,
            "nauo_count": self.nauo_count,
            "complexity": asdict(self.complexity),
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_comments(text: str) -> str:
    """Remove STEP /* ... */ block comments."""
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)


def _data_section(text: str) -> str:
    """
    Extract the DATA; … ENDSEC; block and collapse all whitespace to single
    spaces so that multi-line entity definitions match single-line regex patterns.
    """
    start = text.find("DATA;")
    if start == -1:
        return " ".join(text.split())
    end = text.find("ENDSEC;", start)
    section = text[start:end] if end != -1 else text[start:]
    return " ".join(section.split())


def _f(v: str) -> float:
    """Parse a STEP float token."""
    return float(v)


def _normalise(v: list[float]) -> list[float]:
    mag = math.sqrt(sum(c * c for c in v))
    return [c / mag for c in v] if mag > 1e-10 else v


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _to_mm(value: float, units: str) -> float:
    """Convert a coordinate value to millimetres based on the detected unit system."""
    if units == "inch":
        return value * 25.4
    if units == "m":
        return value * 1_000.0
    if units == "cm":
        return value * 10.0
    return value  # already mm (or unknown — assume mm)


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------


def _detect_units(header: str, data_prefix: str) -> str:
    """
    Detect the length unit from the STEP header and the first part of the DATA section.
    Checks in priority order: inch → cm → mm → m → unknown.
    """
    combined = header + " " + data_prefix
    if _RE_INCH.search(combined):
        return "inch"
    if _RE_SI_CENTI_METRE.search(combined):
        return "cm"
    if _RE_SI_MILLI_METRE.search(combined):
        return "mm"
    if _RE_SI_METRE.search(combined):
        return "m"
    return "unknown"


def _extract_cartesian_points(data: str) -> dict[int, tuple[float, float, float]]:
    """Parse all CARTESIAN_POINT entities. Returns {entity_id: (x, y, z)}."""
    result: dict[int, tuple[float, float, float]] = {}
    for m in _RE_CARTESIAN.finditer(data):
        try:
            result[int(m.group(1))] = (_f(m.group(2)), _f(m.group(3)), _f(m.group(4)))
        except ValueError:
            pass
    return result


def _extract_directions(data: str) -> dict[int, list[float]]:
    """Parse DIRECTION entities. Returns {entity_id: normalised [dx, dy, dz]}."""
    result: dict[int, list[float]] = {}
    for m in _RE_DIRECTION.finditer(data):
        try:
            v = [_f(m.group(2)), _f(m.group(3)), _f(m.group(4))]
            result[int(m.group(1))] = _normalise(v)
        except ValueError:
            pass
    return result


def _extract_axis_placements(data: str) -> dict[int, dict[str, int | None]]:
    """
    Parse AXIS2_PLACEMENT_3D entities.
    Returns {entity_id: {"loc": int, "axis": int, "refdir": int|None}}.
    """
    result: dict[int, dict[str, int | None]] = {}
    for m in _RE_AXIS2P3D.finditer(data):
        try:
            result[int(m.group(1))] = {
                "loc": int(m.group(2)),
                "axis": int(m.group(3)),
                "refdir": int(m.group(4)) if m.group(4) else None,
            }
        except ValueError:
            pass
    return result


def _compute_bbox(
    points: dict[int, tuple[float, float, float]],
    units: str,
) -> BoundingBox | None:
    """
    Compute the axis-aligned bounding box from all parsed CARTESIAN_POINT coordinates.

    Note: this includes ALL coordinate data (including B-spline control points),
    so the result may be a slight overestimate of the true tight bounding box.
    All values are converted to mm.
    """
    if not points:
        return None

    vals = list(points.values())
    xs = [_to_mm(p[0], units) for p in vals]
    ys = [_to_mm(p[1], units) for p in vals]
    zs = [_to_mm(p[2], units) for p in vals]

    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)

    # Guard against degenerate (flat) geometry
    dx = max(dx, 0.001)
    dy = max(dy, 0.001)
    dz = max(dz, 0.001)

    diag = math.sqrt(dx**2 + dy**2 + dz**2)
    return BoundingBox(
        x=round(dx, 4),
        y=round(dy, 4),
        z=round(dz, 4),
        diagonal=round(diag, 4),
    )


def _extract_circles(data: str) -> list[dict[str, Any]]:
    """Parse CIRCLE entities. Returns list of {eid, axis_ref, radius}."""
    result = []
    for m in _RE_CIRCLE.finditer(data):
        try:
            result.append({
                "eid": int(m.group(1)),
                "axis_ref": int(m.group(2)),
                "radius": _f(m.group(3)),
            })
        except ValueError:
            pass
    return result


def _resolve_holes(
    circles: list[dict[str, Any]],
    axis_placements: dict[int, dict[str, int | None]],
    cart_points: dict[int, tuple[float, float, float]],
    directions: dict[int, list[float]],
    units: str,
) -> list[HoleFeature]:
    """
    Resolve CIRCLE entities into HoleFeature objects.

    Algorithm:
    1. For each CIRCLE, follow the reference chain:
       CIRCLE.axis_ref → AXIS2_PLACEMENT_3D → location (CARTESIAN_POINT) + axis (DIRECTION)
    2. Group circles that share the same radius (±5%) and parallel axis (|dot| > 0.99).
       Each such group is one cylindrical hole (or boss).
    3. Compute depth as the span of circle-center projections along the hole axis.
    """
    # Step 1: resolve each circle to a position and axis direction
    resolved: list[dict[str, Any]] = []
    for c in circles:
        ap = axis_placements.get(c["axis_ref"])
        if ap is None:
            continue
        loc = cart_points.get(ap["loc"])          # type: ignore[arg-type]
        axis_dir = directions.get(ap["axis"])     # type: ignore[arg-type]
        if loc is None or axis_dir is None:
            continue
        resolved.append({
            "radius": _to_mm(c["radius"], units),
            "center": [_to_mm(coord, units) for coord in loc],
            "axis": axis_dir,
        })

    if not resolved:
        return []

    # Step 2: group by radius and axis direction
    used = [False] * len(resolved)
    groups: list[list[dict[str, Any]]] = []

    for i, ci in enumerate(resolved):
        if used[i]:
            continue
        group = [ci]
        used[i] = True
        for j in range(i + 1, len(resolved)):
            if used[j]:
                continue
            cj = resolved[j]
            # Radius match within 5%
            ratio = ci["radius"] / cj["radius"] if cj["radius"] > 1e-6 else 999.0
            if not (0.95 <= ratio <= 1.05):
                continue
            # Axis parallel (same or opposite direction)
            if abs(_dot(ci["axis"], cj["axis"])) < 0.99:
                continue
            group.append(cj)
            used[j] = True
        groups.append(group)

    # Step 3: build HoleFeature for each group
    holes: list[HoleFeature] = []
    for idx, group in enumerate(groups):
        rep = group[0]
        radius = round(rep["radius"], 4)
        axis = rep["axis"]

        # Depth: project each circle center onto the axis and take the range
        projections = [_dot(c["center"], axis) for c in group]
        span = max(projections) - min(projections) if len(projections) > 1 else 0.0
        depth = round(span, 4) if span > 0.001 else None

        # Centroid of circle centers
        n = len(group)
        center_avg = [
            round(sum(c["center"][k] for c in group) / n, 4)
            for k in range(3)
        ]

        holes.append(HoleFeature(
            index=idx,
            radius_mm=radius,
            diameter_mm=round(radius * 2, 4),
            axis=axis,
            depth_mm=depth,
            center=center_avg,
        ))

    # Sort largest diameter first (most significant features first)
    holes.sort(key=lambda h: h.diameter_mm, reverse=True)
    return holes


def _extract_surface_counts(data: str) -> SurfaceCounts:
    return SurfaceCounts(
        plane       =len(_RE_PLANE.findall(data)),
        cylindrical =len(_RE_CYLINDRICAL.findall(data)),
        conical     =len(_RE_CONICAL.findall(data)),
        spherical   =len(_RE_SPHERICAL.findall(data)),
        toroidal    =len(_RE_TOROIDAL.findall(data)),
        b_spline    =len(_RE_BSPLINE.findall(data)),
        other       =0,
    )


def _extract_products(data: str) -> list[str]:
    """Return a list of unique, non-empty PRODUCT names (up to 100)."""
    names: list[str] = []
    seen: set[str] = set()
    for m in _RE_PRODUCT.finditer(data):
        name = m.group(3).strip()  # PRODUCT('id', 'NAME', ...)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
        if len(names) >= 100:
            break
    return names


def _extract_solid_count(data: str) -> int:
    """Count MANIFOLD_SOLID_BREP entities; fall back to PRODUCT_DEFINITION_SHAPE count."""
    n = len(_RE_MANIFOLD_BREP.findall(data))
    if n == 0:
        n = len(_RE_PROD_DEF_SHAPE.findall(data))
    return max(1, n)


def _compute_complexity(data: str, face_count: int) -> ComplexityInfo:
    # Rough entity count: number of '#' characters in the data section
    # divided by 2 (each entity appears as a definition and as references).
    entity_count = data.count("#") // 2
    score = (face_count * 5) + (entity_count // 10)
    label = (
        "LOW" if score < _COMPLEXITY_LOW_MAX
        else "MED" if score < _COMPLEXITY_MED_MAX
        else "HIGH"
    )
    return ComplexityInfo(
        entity_count=entity_count,
        face_count=face_count,
        score=score,
        label=label,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_step_geometry(path: Path | str) -> StepGeometryResult:
    """
    Parse a STEP file and return a StepGeometryResult.

    All fields degrade gracefully: if an entity type is absent or unparseable
    the corresponding field becomes None / empty list / 0 rather than raising.

    Raises
    ------
    FileNotFoundError  if the file does not exist.
    ValueError         if the file does not have a .step / .stp extension.
    RuntimeError       if the file cannot be read.
    """
    path = Path(path)
    warnings: list[str] = []

    if not path.exists():
        raise FileNotFoundError(f"STEP file not found: {path}")

    ext = path.suffix.lower().lstrip(".")
    if ext not in {"step", "stp"}:
        raise ValueError(f"Expected .step or .stp extension, got: {path.suffix!r}")

    size_bytes = path.stat().st_size

    if size_bytes > _MAX_FILE_BYTES:
        warnings.append(
            f"File size ({size_bytes // 1024 // 1024} MB) exceeds the "
            f"{_MAX_FILE_BYTES // 1024 // 1024} MB read limit; "
            "geometry extraction may be incomplete."
        )

    try:
        text = _strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read STEP file: {exc}") from exc

    # Split file into header (before DATA;) and data section
    data_start_idx = text.find("DATA;")
    header = text[:data_start_idx] if data_start_idx != -1 else text[:4000]

    # Collapse the DATA section to single-line for robust regex matching
    data = _data_section(text)

    # -----------------------------------------------------------------------
    # Unit detection
    # -----------------------------------------------------------------------
    units = _detect_units(header, data[:8000])
    if units == "unknown":
        warnings.append(
            "Could not determine unit system from STEP header. "
            "Assuming millimetres; bounding box may be incorrect if the file uses inches."
        )

    # -----------------------------------------------------------------------
    # Coordinate entities
    # -----------------------------------------------------------------------
    cart_points     = _extract_cartesian_points(data)
    directions      = _extract_directions(data)
    axis_placements = _extract_axis_placements(data)
    circles         = _extract_circles(data)

    # -----------------------------------------------------------------------
    # Bounding box
    # -----------------------------------------------------------------------
    bbox = _compute_bbox(cart_points, units)
    if not cart_points:
        warnings.append(
            "No CARTESIAN_POINT entities found. "
            "The file may use a non-standard STEP schema or be corrupted."
        )

    # -----------------------------------------------------------------------
    # Volume (bounding-box estimate, in mm³)
    # -----------------------------------------------------------------------
    volume_mm3: float | None = None
    if bbox:
        volume_mm3 = round(bbox.x * bbox.y * bbox.z, 2)

    # -----------------------------------------------------------------------
    # Solid / part count
    # -----------------------------------------------------------------------
    solid_count = _extract_solid_count(data)
    part_count  = solid_count

    # -----------------------------------------------------------------------
    # Holes
    # -----------------------------------------------------------------------
    holes = _resolve_holes(circles, axis_placements, cart_points, directions, units)

    # -----------------------------------------------------------------------
    # Surface types
    # -----------------------------------------------------------------------
    surfaces = _extract_surface_counts(data)

    # -----------------------------------------------------------------------
    # Threads
    # -----------------------------------------------------------------------
    has_threads   = bool(_RE_HELICOIDAL.search(data))
    thread_hints: list[str] = []
    if has_threads:
        thread_hints.append("HELICOIDAL_SURFACE entity detected")

    # -----------------------------------------------------------------------
    # Assembly / component names
    # -----------------------------------------------------------------------
    component_names = _extract_products(data)
    nauo_count      = len(_RE_NAUO.findall(data))

    # -----------------------------------------------------------------------
    # Complexity
    # -----------------------------------------------------------------------
    face_count = len(_RE_ADVANCED_FACE.findall(data))
    complexity = _compute_complexity(data, face_count)

    return StepGeometryResult(
        filename        =path.name,
        size_bytes      =size_bytes,
        units           =units if units != "unknown" else "mm",  # assume mm in output
        bbox            =bbox,
        volume_mm3      =volume_mm3,
        solid_count     =solid_count,
        part_count      =part_count,
        holes           =holes,
        surfaces        =surfaces,
        has_threads     =has_threads,
        thread_hints    =thread_hints,
        component_names =component_names,
        nauo_count      =nauo_count,
        complexity      =complexity,
        warnings        =warnings,
    )


def geometry_meta_from_step(path: Path | str) -> dict[str, Any]:
    """
    Convenience wrapper: parse a STEP file and return a dict compatible
    with the existing geometry_meta_json field in UploadFile.meta.

    Returns a safe fallback dict on any error rather than propagating exceptions.
    """
    try:
        return extract_step_geometry(path).to_geometry_meta()
    except Exception as exc:
        return {
            "units": "mm",
            "bbox": None,
            "diagonal": None,
            "part_count": 1,
            "volume": None,
            "triangle_count": None,
            "holes": [],
            "surfaces": {},
            "has_threads": False,
            "thread_hints": [],
            "component_names": [],
            "nauo_count": 0,
            "complexity": {},
            "warnings": [f"Extraction failed: {exc}"],
            "error": str(exc),
        }
