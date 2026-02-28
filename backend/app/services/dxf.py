from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, radians, sin
from typing import Iterable, Optional

import ezdxf
from ezdxf.colors import aci2rgb


@dataclass
class Bounds:
    min_x: float | None = None
    min_y: float | None = None
    max_x: float | None = None
    max_y: float | None = None

    def update(self, x: float, y: float) -> None:
        if self.min_x is None or x < self.min_x:
            self.min_x = x
        if self.min_y is None or y < self.min_y:
            self.min_y = y
        if self.max_x is None or x > self.max_x:
            self.max_x = x
        if self.max_y is None or y > self.max_y:
            self.max_y = y

    def merge(self, other: "Bounds") -> None:
        if other.min_x is None:
            return
        self.update(other.min_x, other.min_y)
        self.update(other.max_x, other.max_y)

    def as_dict(self) -> dict:
        if self.min_x is None:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
        }


def _layer_color_hex(aci: int) -> str:
    r, g, b = aci2rgb(aci)
    # ACI 7 is white/black depending viewer bg. We force a visible dark line color.
    if (r, g, b) == (255, 255, 255):
        return "#111827"
    return f"#{r:02x}{g:02x}{b:02x}"


def _color_for_entity(entity, layer_colors: dict[str, str]) -> str:
    try:
        color = int(entity.dxf.color)
    except Exception:
        color = 256
    if color in (0, 256):  # BYBLOCK or BYLAYER
        return layer_colors.get(entity.dxf.layer, "#0f172a")
    return _layer_color_hex(color)


def _bounds_line(entity) -> Bounds:
    b = Bounds()
    start = entity.dxf.start
    end = entity.dxf.end
    b.update(start.x, start.y)
    b.update(end.x, end.y)
    return b


def _bounds_circle(entity) -> Bounds:
    b = Bounds()
    c = entity.dxf.center
    r = float(entity.dxf.radius)
    b.update(c.x - r, c.y - r)
    b.update(c.x + r, c.y + r)
    return b


def _arc_point(center, radius, angle_deg):
    a = radians(angle_deg)
    return (center.x + radius * cos(a), center.y + radius * sin(a))


def _bounds_arc(entity) -> Bounds:
    b = Bounds()
    c = entity.dxf.center
    r = float(entity.dxf.radius)
    start = float(entity.dxf.start_angle)
    end = float(entity.dxf.end_angle)
    b.update(*_arc_point(c, r, start))
    b.update(*_arc_point(c, r, end))

    def _within(a: float) -> bool:
        if start <= end:
            return start <= a <= end
        return a >= start or a <= end

    for a in (0.0, 90.0, 180.0, 270.0):
        if _within(a):
            b.update(*_arc_point(c, r, a))
    return b


def _bounds_polyline(points: Iterable[tuple[float, float]]) -> Bounds:
    b = Bounds()
    for x, y in points:
        b.update(x, y)
    return b


def _polyline_points(entity) -> list[tuple[float, float]]:
    points = []
    try:
        for p in entity.get_points():
            points.append((p[0], p[1]))
    except Exception:
        pass
    return points


def _ellipse_points(entity, segments: int = 96) -> list[tuple[float, float]]:
    try:
        center = entity.dxf.center
        major_axis = entity.dxf.major_axis
        ratio = float(entity.dxf.ratio or 0.0)
        if ratio <= 0:
            return []

        major_len = hypot(float(major_axis.x), float(major_axis.y))
        if major_len <= 0:
            return []
        rot = atan2(float(major_axis.y), float(major_axis.x))

        start = float(getattr(entity.dxf, "start_param", 0.0))
        end = float(getattr(entity.dxf, "end_param", 2 * pi))
        if end <= start:
            end += 2 * pi

        step = (end - start) / max(segments, 12)
        points: list[tuple[float, float]] = []
        t = start
        while t <= end + 1e-9:
            x_local = major_len * cos(t)
            y_local = (major_len * ratio) * sin(t)
            x = center.x + (x_local * cos(rot) - y_local * sin(rot))
            y = center.y + (x_local * sin(rot) + y_local * cos(rot))
            points.append((x, y))
            t += step
        return points
    except Exception:
        return []


def _spline_points(entity, segments: int = 96) -> list[tuple[float, float]]:
    try:
        tool = entity.construction_tool()
        points = [(float(p.x), float(p.y)) for p in tool.approximate(segments=segments)]
        if points:
            return points
    except Exception:
        pass
    try:
        points = [(float(p[0]), float(p[1])) for p in entity.fit_points]
        if points:
            return points
    except Exception:
        pass
    try:
        points = [(float(p[0]), float(p[1])) for p in entity.control_points]
        if points:
            return points
    except Exception:
        pass
    return []


def load_doc(path: str):
    return ezdxf.readfile(path)


def manifest_from_doc(doc) -> dict:
    layers = []
    layer_colors: dict[str, str] = {}
    for layer in doc.layers:
        color = _layer_color_hex(layer.color)
        layer_colors[layer.dxf.name] = color
        layers.append(
            {
                "name": layer.dxf.name,
                "color": color,
                "linetype": layer.dxf.linetype,
                "is_visible": True,
            }
        )

    entity_counts: dict[str, int] = {}
    bounds = Bounds()
    for e in doc.modelspace():
        etype = e.dxftype()
        entity_counts[etype] = entity_counts.get(etype, 0) + 1
        b = bounds_for_entity(e)
        if b:
            bounds.merge(b)

    units_code = int(doc.header.get("$INSUNITS", 0) or 0)
    units_name = _units_name(units_code)

    return {
        "layers": layers,
        "bbox": bounds.as_dict(),
        "units": {"code": units_code, "name": units_name},
        "entity_counts": entity_counts,
    }


def _units_name(code: int) -> str:
    return {
        0: "unitless",
        1: "inches",
        2: "feet",
        3: "miles",
        4: "millimeters",
        5: "centimeters",
        6: "meters",
        7: "kilometers",
    }.get(code, "unknown")


def bounds_for_entity(entity) -> Optional[Bounds]:
    etype = entity.dxftype()
    if etype == "LINE":
        return _bounds_line(entity)
    if etype in {"LWPOLYLINE", "POLYLINE"}:
        pts = _polyline_points(entity)
        return _bounds_polyline(pts) if pts else None
    if etype == "CIRCLE":
        return _bounds_circle(entity)
    if etype == "ARC":
        return _bounds_arc(entity)
    if etype == "ELLIPSE":
        pts = _ellipse_points(entity)
        return _bounds_polyline(pts) if pts else None
    if etype == "SPLINE":
        pts = _spline_points(entity)
        return _bounds_polyline(pts) if pts else None
    if etype == "POINT":
        try:
            p = entity.dxf.location
            b = Bounds()
            b.update(float(p.x), float(p.y))
            return b
        except Exception:
            return None
    return None


def render_svg(doc, visible_layers: Optional[set[str]] = None) -> str:
    layers = {layer.dxf.name: _layer_color_hex(layer.color) for layer in doc.layers}
    bounds = Bounds()
    entities = []

    for e in doc.modelspace():
        layer = e.dxf.layer
        if visible_layers is not None and layer not in visible_layers:
            continue
        b = bounds_for_entity(e)
        if b:
            bounds.merge(b)
        svg = entity_to_svg(e, layers)
        if svg:
            entities.append(svg)

    bb = bounds.as_dict()
    min_x = bb["min_x"]
    min_y = bb["min_y"]
    max_x = bb["max_x"]
    max_y = bb["max_y"]
    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)
    padding = max(width, height) * 0.02
    min_x -= padding
    min_y -= padding
    width += padding * 2
    height += padding * 2
    stroke_width = max(0.25, min(max(width, height) / 1800.0, 3.0))

    view_box = f"{min_x} {min_y} {width} {height}"
    header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{view_box}" width="100%" height="100%" '
        f'preserveAspectRatio="xMidYMid meet">'
    )
    y_flip_translate = min_y + max_y
    body = f'<g transform="translate(0,{y_flip_translate}) scale(1,-1)">'
    body += "".join(entity_to_svg(e, layers, stroke_width=stroke_width) or "" for e in doc.modelspace() if visible_layers is None or e.dxf.layer in visible_layers)
    body += "</g>"
    footer = "</svg>"
    return header + body + footer


def entity_to_svg(entity, layer_colors: dict[str, str], stroke_width: float = 1.0) -> str | None:
    etype = entity.dxftype()
    color = _color_for_entity(entity, layer_colors)
    stroke = f'stroke="{color}"'
    base = f'{stroke} stroke-width="{stroke_width:.4f}" fill="none" vector-effect="non-scaling-stroke"'

    if etype == "LINE":
        s = entity.dxf.start
        e = entity.dxf.end
        return f'<line x1="{s.x}" y1="{s.y}" x2="{e.x}" y2="{e.y}" {base} />'

    if etype in {"LWPOLYLINE", "POLYLINE"}:
        pts = _polyline_points(entity)
        if not pts:
            return None
        points = " ".join(f"{x},{y}" for x, y in pts)
        return f'<polyline points="{points}" {base} />'

    if etype == "CIRCLE":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        return f'<circle cx="{c.x}" cy="{c.y}" r="{r}" {base} />'

    if etype == "ARC":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        start = float(entity.dxf.start_angle)
        end = float(entity.dxf.end_angle)
        x1, y1 = _arc_point(c, r, start)
        x2, y2 = _arc_point(c, r, end)
        large = 1 if abs(end - start) > 180 else 0
        sweep = 1
        d = f"M {x1} {y1} A {r} {r} 0 {large} {sweep} {x2} {y2}"
        return f'<path d="{d}" {base} />'

    if etype == "ELLIPSE":
        pts = _ellipse_points(entity)
        if not pts:
            return None
        d = " ".join(f"{x},{y}" for x, y in pts)
        return f'<polyline points="{d}" {base} />'

    if etype == "SPLINE":
        pts = _spline_points(entity)
        if not pts:
            return None
        d = " ".join(f"{x},{y}" for x, y in pts)
        return f'<polyline points="{d}" {base} />'

    if etype == "POINT":
        try:
            p = entity.dxf.location
            radius = max(stroke_width * 1.6, 0.4)
            return f'<circle cx="{p.x}" cy="{p.y}" r="{radius}" {base} />'
        except Exception:
            return None

    return None

