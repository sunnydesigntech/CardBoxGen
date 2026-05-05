"""Geometry helpers for laser-cut SVG generation."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]


def fmt(n: float) -> str:
    return f"{float(n):.3f}".rstrip("0").rstrip(".")


def add(p: Point, q: Point) -> Point:
    return (p[0] + q[0], p[1] + q[1])


def sub(p: Point, q: Point) -> Point:
    return (p[0] - q[0], p[1] - q[1])


def mul(p: Point, s: float) -> Point:
    return (p[0] * s, p[1] * s)


def dot(p: Point, q: Point) -> float:
    return p[0] * q[0] + p[1] * q[1]


def polyline_to_path(points: Sequence[Point], close: bool = True) -> str:
    if not points:
        return ""
    d = [f"M {fmt(points[0][0])} {fmt(points[0][1])}"]
    for x, y in points[1:]:
        d.append(f"L {fmt(x)} {fmt(y)}")
    if close:
        d.append("Z")
    return " ".join(d)


def polygon_to_path_with_tabs(points: Sequence[Point], *, tab_width_mm: float) -> str:
    """Render a polygon as an open SVG path with a small holding tab per edge."""

    if len(points) < 3:
        return ""
    tab = max(0.0, float(tab_width_mm))
    if tab <= 0:
        return polyline_to_path(points, close=True)

    ring = list(points)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    cmds = [f"M {fmt(ring[0][0])} {fmt(ring[0][1])}"]
    for p0, p1 in zip(ring, ring[1:]):
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        if abs(dx) > 1e-9 and abs(dy) > 1e-9:
            return polyline_to_path(points, close=True)

        length = abs(dx) + abs(dy)
        if length <= 1e-9:
            continue
        if length <= tab * 2 + 0.5:
            cmds.append(f"L {fmt(p1[0])} {fmt(p1[1])}")
            continue

        ux = 0.0 if abs(dx) < 1e-9 else (1.0 if dx > 0 else -1.0)
        uy = 0.0 if abs(dy) < 1e-9 else (1.0 if dy > 0 else -1.0)
        gap0 = length / 2 - tab / 2
        gap1 = length / 2 + tab / 2
        cut_end = (p0[0] + ux * gap0, p0[1] + uy * gap0)
        resume = (p0[0] + ux * gap1, p0[1] + uy * gap1)

        cmds.append(f"L {fmt(cut_end[0])} {fmt(cut_end[1])}")
        cmds.append(f"M {fmt(resume[0])} {fmt(resume[1])}")
        cmds.append(f"L {fmt(p1[0])} {fmt(p1[1])}")

    return " ".join(cmds)


def bbox_points(points: Sequence[Point]) -> BBox:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def bbox_size(bbox: BBox) -> Point:
    x0, y0, x1, y1 = bbox
    return (x1 - x0, y1 - y0)


def bbox_intersects(a: BBox, b: BBox, *, eps: float = 1e-9) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 <= bx0 + eps or bx1 <= ax0 + eps or ay1 <= by0 + eps or by1 <= ay0 + eps)


def polygon_area(points: Sequence[Point]) -> float:
    if len(points) < 3:
        return 0.0
    a = 0.0
    ring = list(points)
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def translate_points(points: Sequence[Point], dx: float, dy: float) -> List[Point]:
    return [(x + dx, y + dy) for x, y in points]


def is_axis_aligned_dir(v: Point) -> bool:
    return (v[0] == 0 and abs(v[1]) == 1) or (v[1] == 0 and abs(v[0]) == 1)


def outward_normal_for_edge(dirv: Point) -> Point:
    """Outward normal for clockwise polygons in SVG coordinates."""

    dx, dy = dirv
    return (dy, -dx)


def rect_path(x: float, y: float, w: float, h: float) -> str:
    return f"M {fmt(x)} {fmt(y)} L {fmt(x + w)} {fmt(y)} L {fmt(x + w)} {fmt(y + h)} L {fmt(x)} {fmt(y + h)} Z"


def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = max(0.0, min(float(r), w / 2, h / 2))
    if r <= 0:
        return rect_path(x, y, w, h)
    return (
        f"M {fmt(x + r)} {fmt(y)} "
        f"L {fmt(x + w - r)} {fmt(y)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w)} {fmt(y + r)} "
        f"L {fmt(x + w)} {fmt(y + h - r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w - r)} {fmt(y + h)} "
        f"L {fmt(x + r)} {fmt(y + h)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y + h - r)} "
        f"L {fmt(x)} {fmt(y + r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + r)} {fmt(y)} Z"
    )


def circle_path(cx: float, cy: float, r: float) -> str:
    r = max(0.0, float(r))
    if r <= 0:
        return ""
    return (
        f"M {fmt(cx + r)} {fmt(cy)} "
        f"A {fmt(r)} {fmt(r)} 0 1 0 {fmt(cx - r)} {fmt(cy)} "
        f"A {fmt(r)} {fmt(r)} 0 1 0 {fmt(cx + r)} {fmt(cy)} Z"
    )


def thumb_notch_path(w: float, y_top: float, radius: float, depth: float) -> str:
    radius = max(0.0, min(float(radius), float(w) / 2))
    depth = max(0.0, float(depth))
    cx = w / 2
    x0 = cx - radius
    x1 = cx + radius
    y0 = y_top
    y1 = y_top + depth
    return (
        f"M {fmt(x0)} {fmt(y0)} "
        f"L {fmt(x0)} {fmt(y1)} "
        f"A {fmt(radius)} {fmt(radius)} 0 0 0 {fmt(x1)} {fmt(y1)} "
        f"L {fmt(x1)} {fmt(y0)} Z"
    )


def circle_outline(r: float, *, segs: int = 96) -> List[Point]:
    segs = max(12, int(segs))
    return [(r * math.cos(2 * math.pi * i / segs) + r, r * math.sin(2 * math.pi * i / segs) + r) for i in range(segs)]
