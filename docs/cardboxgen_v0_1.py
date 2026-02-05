#!/usr/bin/env python3
"""cardboxgen_v0_1.py

Parametric SVG generator for laser-cut finger-jointed card boxes / trays / dispensers.

Key upgrades vs v0.1:
- Deterministic edge-pairing: every mating edge pair shares ONE computed finger plan
  (count + per-segment widths + start state), and the mate uses the complementary pattern.
  This avoids round() drift and "phase guessing".
- Stable finger count (preferred rule):
    n = max(min_fingers, floor(length / target_finger_w)); then force odd.
  Optional explicit finger counts per edge family (OUTER / VERTICAL).
- Practical kerf + clearance handling for finger widths (in-plane fit):

  Model:
  - External (tab) width after cutting shrinks by ~kerf (two cut edges).
  - Internal (slot) opening grows by ~kerf.

  If we want a target clearance C = (slot_after - tab_after), a symmetric design rule is:
    tab_drawn  = nominal + (kerf - C/2)
    slot_drawn = nominal + (C/2 - kerf)

  Within a finger joint edge, we adjust each segment width accordingly and then
  normalize widths to preserve the exact total edge length.

Notes:
- Geometry is Manhattan / axis-aligned for laser friendliness.
- SVG layers:
  CUT: red stroke 0.2
  SCORE: blue dashed
  ENGRAVE/TEXT: black
- Optional pyclipper kerf offsetting is supported via --offset-kerf if installed.
"""

from __future__ import annotations

import argparse
import json
import math
import textwrap
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

__version__ = "0.2"

Point = Tuple[float, float]


def fmt(n: float) -> str:
    return f"{n:.3f}".rstrip("0").rstrip(".")


def add(p: Point, q: Point) -> Point:
    return (p[0] + q[0], p[1] + q[1])


def sub(p: Point, q: Point) -> Point:
    return (p[0] - q[0], p[1] - q[1])


def mul(p: Point, s: float) -> Point:
    return (p[0] * s, p[1] * s)


def dot(p: Point, q: Point) -> float:
    return p[0] * q[0] + p[1] * q[1]


def polyline_to_path(points: List[Point], close: bool = True) -> str:
    if not points:
        return ""
    d = [f"M {fmt(points[0][0])} {fmt(points[0][1])}"]
    for x, y in points[1:]:
        d.append(f"L {fmt(x)} {fmt(y)}")
    if close:
        d.append("Z")
    return " ".join(d)


def polygon_to_path_with_tabs(points: List[Point], *, tab_width_mm: float) -> str:
    """Render a polygon as an SVG path but with a small gap (holding tab) per edge.

    This leaves material bridges so parts don't drop out of the sheet.
    
    Limitations:
    - Only supports axis-aligned polygon edges.
    - Produces an *open* path (no trailing 'Z') to preserve gaps.
    """

    if not points or len(points) < 3:
        return ""
    tab = max(0.0, float(tab_width_mm))
    if tab <= 0:
        return polyline_to_path(points, close=True)

    # Ensure we iterate over a closed ring.
    ring = list(points)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    cmds: List[str] = []
    cmds.append(f"M {fmt(ring[0][0])} {fmt(ring[0][1])}")

    pen_down = True
    for p0, p1 in zip(ring, ring[1:]):
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        if abs(dx) > 1e-9 and abs(dy) > 1e-9:
            # Not axis-aligned; fall back to closed.
            return polyline_to_path(points, close=True)

        length = abs(dx) + abs(dy)
        if length <= 1e-9:
            continue

        if length <= tab * 2 + 0.5:
            # Too short to tab safely; cut the full edge.
            if not pen_down:
                cmds.append(f"M {fmt(p0[0])} {fmt(p0[1])}")
                pen_down = True
            cmds.append(f"L {fmt(p1[0])} {fmt(p1[1])}")
            continue

        # Leave a gap centered on the edge.
        ux = 0.0 if abs(dx) < 1e-9 else (1.0 if dx > 0 else -1.0)
        uy = 0.0 if abs(dy) < 1e-9 else (1.0 if dy > 0 else -1.0)
        gap0 = length / 2 - tab / 2
        gap1 = length / 2 + tab / 2

        cut_end = (p0[0] + ux * gap0, p0[1] + uy * gap0)
        resume = (p0[0] + ux * gap1, p0[1] + uy * gap1)

        if not pen_down:
            cmds.append(f"M {fmt(p0[0])} {fmt(p0[1])}")
            pen_down = True
        cmds.append(f"L {fmt(cut_end[0])} {fmt(cut_end[1])}")

        cmds.append(f"M {fmt(resume[0])} {fmt(resume[1])}")
        pen_down = True
        cmds.append(f"L {fmt(p1[0])} {fmt(p1[1])}")

    return " ".join(cmds)


def bbox_points(points: List[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def polygon_area(points: List[Point]) -> float:
    if len(points) < 3:
        return 0.0
    a = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + [points[0]]):
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def translate_points(points: List[Point], dx: float, dy: float) -> List[Point]:
    return [(x + dx, y + dy) for x, y in points]


def is_axis_aligned_dir(v: Point) -> bool:
    return (v[0] == 0 and abs(v[1]) == 1) or (v[1] == 0 and abs(v[0]) == 1)


def outward_normal_for_edge(dirv: Point) -> Point:
    """Outward normal for a clockwise polygon in SVG coordinates (y down).

    For direction (dx,dy), outward is (dy, -dx).
    """

    dx, dy = dirv
    return (dy, -dx)


class EdgeFamily:
    OUTER = "outer"      # bottom-to-walls
    VERTICAL = "vertical"  # wall-to-wall


def joint_depths_drawn(*, thickness: float, kerf_mm: float, clearance_mm: float) -> Tuple[float, float]:
        """Compute drawn joint depths for tabs vs slots.

        Student-facing expectation (primary rule):
            final_slot ≈ drawn_slot + kerf
            target_final_slot = thickness + clearance
            => drawn_slot = thickness + clearance − kerf

        We keep tab depth nominal (material thickness) and expand/shrink slots to control fit.
        """

        t = float(thickness)
        k = float(kerf_mm)
        c = float(clearance_mm)
        tab_depth = max(0.0, t)
        slot_depth = max(0.0, t + c - k)
        return tab_depth, slot_depth


@dataclass(frozen=True)
class EdgeKey:
    panel: str
    edge: str


@dataclass
class FingerPlan:
    length: float
    count: int
    widths: List[float]
    start_with_tab_on_a: bool

    def tabs_mask_for_a(self) -> List[bool]:
        return [((i % 2 == 0) if self.start_with_tab_on_a else (i % 2 == 1)) for i in range(self.count)]


def compute_finger_count(
    length: float,
    target_finger_w: float,
    *,
    min_fingers: int = 3,
    force_odd: bool = True,
    explicit: Optional[int] = None,
) -> int:
    if length <= 0:
        return 0
    if explicit is not None:
        n = int(explicit)
        if n < 1:
            raise ValueError("explicit finger count must be >= 1")
    else:
        denom = max(1e-6, float(target_finger_w))
        n = int(math.floor(length / denom))
        n = max(int(min_fingers), n)
    if force_odd and (n % 2 == 0):
        n += 1
    return n


def build_finger_plan(
    length: float,
    *,
    count: int,
    kerf_mm: float,
    clearance_mm: float,
    start_with_tab_on_a: bool,
) -> FingerPlan:
    if count <= 0:
        raise ValueError("finger count must be positive")
    # Deterministic uniform pitch; kerf/clearance are handled in *depth*.
    pitch = length / count
    widths = [pitch] * count
    widths[-1] += (length - sum(widths))
    return FingerPlan(length=length, count=count, widths=widths, start_with_tab_on_a=start_with_tab_on_a)


def finger_edge_points(
    start: Point,
    dirv: Point,
    normal_out: Point,
    plan: FingerPlan,
    *,
    thickness: float,
    kerf_mm: float,
    clearance_mm: float,
    invert_tabs: bool,
) -> List[Point]:
    """Generate a Manhattan polyline along an edge using a FingerPlan.

    Returns points excluding the `start` point (so callers can stitch edges).
    The returned sequence ends on the baseline endpoint.
    """

    if plan.length <= 0:
        return []
    if not is_axis_aligned_dir(dirv) or not is_axis_aligned_dir(normal_out):
        raise ValueError("dirv/normal must be axis-aligned")
    if abs(dot(dirv, normal_out)) > 1e-9:
        raise ValueError("dirv and normal must be perpendicular")

    tab_depth, slot_depth = joint_depths_drawn(thickness=thickness, kerf_mm=kerf_mm, clearance_mm=clearance_mm)

    tabs_a = plan.tabs_mask_for_a()
    pts: List[Point] = []
    p = start
    for i, w in enumerate(plan.widths):
        is_tab = tabs_a[i]
        if invert_tabs:
            is_tab = not is_tab
        depth = tab_depth if is_tab else slot_depth
        off = mul(normal_out, depth if is_tab else -depth)
        p_out = add(p, off)
        p2 = add(p, mul(dirv, w))
        p2_out = add(p2, off)

        pts.append(p_out)
        pts.append(p2_out)
        pts.append(p2)
        p = p2
    return pts


@dataclass
class CutPath:
    """Cut path representation.

    If points is provided, it is a closed polygon. If d is provided, it is an SVG path.
    """

    points: Optional[List[Point]] = None
    d: Optional[str] = None

    def to_svg_d(self) -> str:
        if self.d is not None:
            return self.d
        if self.points is None:
            return ""
        return polyline_to_path(self.points, close=True)


@dataclass
class Panel:
    name: str
    outline: List[Point]
    cutouts: List[CutPath] = field(default_factory=list)
    labels: List[Tuple[str, Point]] = field(default_factory=list)

    def bbox(self) -> Tuple[float, float]:
        x0, y0, x1, y1 = bbox_points(self.outline)
        return (x1 - x0, y1 - y0)


def make_window_cutout(w: float, h: float, margin: float, corner_r: float = 0.0) -> CutPath:
    x = margin
    y = margin
    ww = max(1.0, w - 2 * margin)
    hh = max(1.0, h - 2 * margin)
    if corner_r <= 0:
        pts = [(x, y), (x + ww, y), (x + ww, y + hh), (x, y + hh)]
        return CutPath(points=pts)
    r = min(corner_r, ww / 2, hh / 2)
    d = (
        f"M {fmt(x + r)} {fmt(y)} "
        f"L {fmt(x + ww - r)} {fmt(y)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + ww)} {fmt(y + r)} "
        f"L {fmt(x + ww)} {fmt(y + hh - r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + ww - r)} {fmt(y + hh)} "
        f"L {fmt(x + r)} {fmt(y + hh)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y + hh - r)} "
        f"L {fmt(x)} {fmt(y + r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + r)} {fmt(y)} Z"
    )
    return CutPath(d=d)


def make_thumb_notch(w: float, y_top: float, radius: float, depth: float) -> CutPath:
    cx = w / 2
    x0 = cx - radius
    x1 = cx + radius
    y0 = y_top
    y1 = y_top + depth
    d = (
        f"M {fmt(x0)} {fmt(y0)} "
        f"L {fmt(x0)} {fmt(y1)} "
        f"A {fmt(radius)} {fmt(radius)} 0 0 0 {fmt(x1)} {fmt(y1)} "
        f"L {fmt(x1)} {fmt(y0)} Z"
    )
    return CutPath(d=d)


def make_rect_cutout(x: float, y: float, w: float, h: float) -> CutPath:
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return CutPath(points=pts)


def arrange_panels(
    panels: List[Panel],
    *,
    gap: float = 12.0,
    sheet_width: float = 320.0,
    margin: float = 10.0,
):
    placed = []
    x = float(margin)
    y = float(margin)
    row_h = 0.0
    total_w = float(margin)
    total_h = float(margin)
    for p in panels:
        bw, bh = p.bbox()
        if placed and (x + bw > sheet_width - margin):
            x = float(margin)
            y += row_h + gap
            row_h = 0.0
        placed.append((p, x, y))
        x += bw + gap
        row_h = max(row_h, bh)
        total_w = max(total_w, x)
        total_h = max(total_h, y + row_h)
    return placed, total_w + margin, total_h + margin


def svg_header(width: float, height: float) -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{fmt(width)}mm\" height=\"{fmt(height)}mm\" viewBox=\"0 0 {fmt(width)} {fmt(height)}\">\n"
        f"  <desc>Generated by cardboxgen v{__version__}</desc>\n"
    )


def svg_footer() -> str:
    return "</svg>\n"


def svg_layer_styles(*, stroke_mm: float = 0.2) -> str:
    s = max(0.001, float(stroke_mm))
    return (
        "  <style>\n"
        f"    .cut {{ fill: none; stroke: #ff0000; stroke-width: {fmt(s)}; }}\n"
        f"    .score {{ fill: none; stroke: #0000ff; stroke-width: {fmt(s)}; stroke-dasharray: 2 2; }}\n"
        f"    .engrave {{ fill: none; stroke: #000000; stroke-width: {fmt(s)}; }}\n"
        "    .text { fill: #000000; font-family: Arial, sans-serif; font-size: 4px; }\n"
        "  </style>\n"
    )


def try_import_pyclipper():
    try:
        import pyclipper  # type: ignore

        return pyclipper
    except Exception:
        return None


def offset_polygon_pyclipper(points: List[Point], delta: float) -> Optional[List[Point]]:
    pc = try_import_pyclipper()
    if pc is None:
        return None
    if len(points) < 3:
        return None
    scale = 1000.0
    path = [(int(round(x * scale)), int(round(y * scale))) for x, y in points]
    co = pc.PyclipperOffset()
    co.AddPath(path, pc.JT_MITER, pc.ET_CLOSEDPOLYGON)
    res = co.Execute(delta * scale)
    if not res:
        return None
    # choose the largest area result
    def area_i(poly):
        a = 0
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            a += x0 * y1 - x1 * y0
        return abs(a)

    best = max(res, key=area_i)
    return [(p[0] / scale, p[1] / scale) for p in best]


def make_svg(
    panels: List[Panel],
    *,
    meta: dict,
    sheet_width: float,
    labels: bool,
    offset_kerf: bool,
    kerf_mm: float,
    layout_margin_mm: float = 10.0,
    layout_padding_mm: float = 12.0,
    stroke_mm: float = 0.2,
    holding_tabs: bool = False,
    tab_width_mm: float = 2.0,
) -> str:
    placed, W, H = arrange_panels(
        panels,
        sheet_width=sheet_width,
        margin=float(layout_margin_mm),
        gap=float(layout_padding_mm),
    )
    meta_comment = "\n".join(textwrap.wrap(json.dumps(meta, ensure_ascii=False), width=120))
    out: List[str] = [svg_header(W, H), svg_layer_styles(stroke_mm=stroke_mm)]
    out.append(f"  <!-- params: {meta_comment} -->\n")

    label_items: List[Tuple[str, float, float]] = []

    out.append('  <g id="CUT" class="cut">\n')
    for p, x, y in placed:
        outline_pts = p.outline
        if offset_kerf:
            off = offset_polygon_pyclipper(outline_pts, +kerf_mm / 2.0)
            if off is not None:
                outline_pts = off

        # Compensate for outlines that extend into negative coordinates due to finger protrusions.
        minx, miny, _, _ = bbox_points(outline_pts)
        gx = x - minx
        gy = y - miny
        out.append(f'    <g id="{p.name}" transform="translate({fmt(gx)},{fmt(gy)})">\n')

        if holding_tabs:
            out.append(
                f'      <path d="{polygon_to_path_with_tabs(outline_pts, tab_width_mm=tab_width_mm)}"/>\n'
            )
        else:
            out.append(f'      <path d="{polyline_to_path(outline_pts, close=True)}"/>\n')
        for c in p.cutouts:
            if c.points is not None:
                pts = c.points
                if offset_kerf:
                    off = offset_polygon_pyclipper(pts, -kerf_mm / 2.0)
                    if off is not None:
                        pts = off
                if holding_tabs:
                    out.append(
                        f'      <path d="{polygon_to_path_with_tabs(pts, tab_width_mm=tab_width_mm)}"/>\n'
                    )
                else:
                    out.append(f'      <path d="{polyline_to_path(pts, close=True)}"/>\n')
            else:
                out.append(f'      <path d="{c.to_svg_d()}"/>\n')
        out.append("    </g>\n")

        if labels:
            for txt, (tx, ty) in p.labels:
                label_items.append((txt, gx + tx, gy + ty))
    out.append("  </g>\n")

    if labels and label_items:
        out.append('  <g id="ENGRAVE" class="text">\n')
        for txt, lx, ly in label_items:
            out.append(f'    <text x="{fmt(lx)}" y="{fmt(ly)}" text-anchor="middle" dominant-baseline="middle">{txt}</text>\n')
        out.append("  </g>\n")
    out.append(svg_footer())
    return "".join(out)


@dataclass
class JointParams:
    thickness: float = 3.0
    target_finger_w: float = 12.0
    min_fingers: int = 3
    kerf_mm: float = 0.2
    clearance_mm: float = 0.15
    finger_count_outer: Optional[int] = None
    finger_count_vertical: Optional[int] = None


@dataclass
class BoxParams:
    # Back-compat
    variant: str = "A"

    # New
    preset: str = "box_with_lid"

    inner_width: float = 70.0
    inner_depth: float = 95.0
    inner_height: float = 120.0
    thickness: float = 3.0

    kerf_mm: float = 0.20
    clearance_mm: float = 0.15

    finger_width: Optional[float] = None
    min_fingers: int = 3
    finger_count_outer: Optional[int] = None
    finger_count_vertical: Optional[int] = None

    # Lid
    lid: bool = True
    lid_height: float = 25.0
    lid_clearance: float = 0.4

    # Front patterns
    front_height: Optional[float] = None
    scoop: bool = False
    scoop_radius: float = 22.0
    scoop_depth: float = 18.0

    slot_width: float = 80.0
    slot_height: float = 18.0
    slot_y_from_bottom: float = 35.0

    window_margin: float = 18.0
    window_corner_r: float = 6.0
    thumb_notch_radius: float = 10.0
    thumb_notch_depth: float = 8.0

    labels: bool = True
    sheet_width: float = 320.0
    layout_margin_mm: float = 10.0
    layout_padding_mm: float = 12.0
    stroke_mm: float = 0.2
    export: str = "single_svg"  # single_svg | per_panel_svgs
    offset_kerf: bool = False
    holding_tabs: bool = False
    tab_width_mm: float = 2.0


@dataclass
class EdgePair:
    """A mating edge pair. FingerPlan is shared."""

    id: str
    family: str
    a: EdgeKey
    b: EdgeKey
    length: float
    plan: FingerPlan


def validate_params_and_pairs(p: BoxParams, edge_pairs: Dict[str, EdgePair]) -> List[str]:
    warnings: List[str] = []

    if p.thickness <= 0:
        warnings.append("Thickness must be > 0")
    if p.kerf_mm < 0:
        warnings.append("Kerf should be >= 0")
    if p.kerf_mm >= p.thickness:
        warnings.append("Kerf is greater than or equal to thickness (check units)")
    if abs(p.clearance_mm) > max(1.0, 0.6 * p.thickness):
        warnings.append("Joint clearance is large relative to thickness")

    tab_d, slot_d = joint_depths_drawn(thickness=p.thickness, kerf_mm=p.kerf_mm, clearance_mm=p.clearance_mm)
    if slot_d <= 0.1:
        warnings.append("Computed drawn slot depth is near zero; joint may not work")
    if tab_d <= 0.1:
        warnings.append("Computed tab depth is near zero; joint may not work")

    for pair in edge_pairs.values():
        if pair.plan.count <= 0:
            warnings.append(f"Edge pair {pair.id} has no fingers")
            continue
        pitch = pair.length / pair.plan.count
        if pitch < 6.0:
            warnings.append(f"Edge pair {pair.id}: tabs are very small (pitch {pitch:.1f}mm)")
        if pitch < p.thickness * 1.2:
            warnings.append(f"Edge pair {pair.id}: pitch is close to thickness (may be fragile)")
    return warnings


@dataclass
class PanelEdge:
    name: str
    start: Point
    dirv: Point
    length: float
    finger_pair_id: Optional[str] = None
    invert_tabs: bool = False


@dataclass
class PanelSpec:
    name: str
    width: float
    height: float
    edges: List[PanelEdge]
    cutouts: List[CutPath] = field(default_factory=list)
    labels: List[Tuple[str, Point]] = field(default_factory=list)


def build_rect_panel_spec(name: str, w: float, h: float) -> PanelSpec:
    p0 = (0.0, 0.0)
    p1 = (w, 0.0)
    p2 = (w, h)
    p3 = (0.0, h)
    edges = [
        PanelEdge("top", start=p0, dirv=(1, 0), length=w),
        PanelEdge("right", start=p1, dirv=(0, 1), length=h),
        PanelEdge("bottom", start=p2, dirv=(-1, 0), length=w),
        PanelEdge("left", start=p3, dirv=(0, -1), length=h),
    ]
    return PanelSpec(name=name, width=w, height=h, edges=edges)


def render_panel_from_spec(spec: PanelSpec, *, joint_params: JointParams, edge_pairs: Dict[str, EdgePair]) -> Panel:
    # Build clockwise outline by stitching edges.
    pts: List[Point] = [spec.edges[0].start]
    for e in spec.edges:
        start = e.start
        dirv = e.dirv
        normal = outward_normal_for_edge(dirv)
        if e.finger_pair_id is None:
            end = add(start, mul(dirv, e.length))
            pts.append(end)
            continue
        pair = edge_pairs[e.finger_pair_id]
        seg_pts = finger_edge_points(
            start,
            dirv,
            normal,
            pair.plan,
            thickness=joint_params.thickness,
            kerf_mm=joint_params.kerf_mm,
            clearance_mm=joint_params.clearance_mm,
            invert_tabs=e.invert_tabs,
        )
        pts.extend(seg_pts)

    # Ensure closed-ish (path writer closes). Also drop consecutive duplicates.
    compact: List[Point] = []
    for p in pts:
        if not compact or (abs(p[0] - compact[-1][0]) > 1e-9 or abs(p[1] - compact[-1][1]) > 1e-9):
            compact.append(p)

    return Panel(name=spec.name, outline=compact, cutouts=list(spec.cutouts), labels=list(spec.labels))


def build_edge_pairs_for_box(
    *,
    joint: JointParams,
    outer_w: float,
    outer_d: float,
    wall_h: float,
    front_h: float,
    include_front: bool,
) -> Dict[str, EdgePair]:
    """Create edge pairs for the base box.

    Convention: the edge pair itself is the source of truth for count/pitch.
    Panel edges reference pair ids and set invert_tabs accordingly.
    """

    pairs: Dict[str, EdgePair] = {}

    def mk_pair(pid: str, family: str, a: EdgeKey, b: EdgeKey, length: float, start_with_tab_on_a: bool):
        explicit = joint.finger_count_outer if family == EdgeFamily.OUTER else joint.finger_count_vertical
        n = compute_finger_count(length, joint.target_finger_w, min_fingers=joint.min_fingers, explicit=explicit)
        plan = build_finger_plan(length, count=n, kerf_mm=joint.kerf_mm, clearance_mm=joint.clearance_mm, start_with_tab_on_a=start_with_tab_on_a)
        pairs[pid] = EdgePair(id=pid, family=family, a=a, b=b, length=length, plan=plan)

    # Bottom-to-walls (outer) pairs.
    mk_pair("bottom_back", EdgeFamily.OUTER, EdgeKey("BOTTOM", "top"), EdgeKey("BACK", "bottom"), outer_w, True)
    mk_pair("bottom_front", EdgeFamily.OUTER, EdgeKey("BOTTOM", "bottom"), EdgeKey("FRONT", "bottom"), outer_w, True)
    mk_pair("bottom_left", EdgeFamily.OUTER, EdgeKey("BOTTOM", "left"), EdgeKey("LEFT", "bottom"), outer_d, True)
    mk_pair("bottom_right", EdgeFamily.OUTER, EdgeKey("BOTTOM", "right"), EdgeKey("RIGHT", "bottom"), outer_d, True)

    # Wall-to-wall (vertical) pairs (corners). We pair full height; if front is lowered,
    # the portion above front_h is a free edge (not paired).
    mk_pair("corner_back_left", EdgeFamily.VERTICAL, EdgeKey("BACK", "left"), EdgeKey("LEFT", "right"), wall_h, True)
    mk_pair("corner_back_right", EdgeFamily.VERTICAL, EdgeKey("BACK", "right"), EdgeKey("RIGHT", "left"), wall_h, True)
    if include_front:
        mk_pair("corner_front_left", EdgeFamily.VERTICAL, EdgeKey("FRONT", "left"), EdgeKey("LEFT", "left"), front_h, True)
        mk_pair("corner_front_right", EdgeFamily.VERTICAL, EdgeKey("FRONT", "right"), EdgeKey("RIGHT", "right"), front_h, True)
    return pairs


def build_panels_for_preset(p: BoxParams) -> List[Panel]:
    t = p.thickness
    outer_w = p.inner_width + 2 * t
    outer_d = p.inner_depth + 2 * t
    wall_h = p.inner_height + t

    target_finger_w = p.finger_width if p.finger_width is not None else max(10.0, 3.0 * t)
    joint = JointParams(
        thickness=t,
        target_finger_w=target_finger_w,
        min_fingers=p.min_fingers,
        kerf_mm=p.kerf_mm,
        clearance_mm=p.clearance_mm,
        finger_count_outer=p.finger_count_outer,
        finger_count_vertical=p.finger_count_vertical,
    )

    preset = p.preset
    include_front = preset in ("dispenser_slot_front", "window_front", "tray_open_front", "box_with_lid")

    front_h = p.front_height if p.front_height is not None else wall_h
    if preset == "tray_open_front":
        # Default: lower front, but keep back full height.
        front_h = p.front_height if p.front_height is not None else max(t * 2, 0.55 * wall_h)
    elif preset in ("dispenser_slot_front", "window_front", "box_with_lid"):
        front_h = wall_h

    edge_pairs = build_edge_pairs_for_box(
        joint=joint,
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
        front_h=front_h,
        include_front=include_front,
    )

    # Panel specs
    bottom = build_rect_panel_spec("BOTTOM", outer_w, outer_d)
    back = build_rect_panel_spec("BACK", outer_w, wall_h)
    left = build_rect_panel_spec("LEFT", outer_d, wall_h)
    right = build_rect_panel_spec("RIGHT", outer_d, wall_h)
    specs: Dict[str, PanelSpec] = {s.name: s for s in [bottom, back, left, right]}

    if include_front:
        front = build_rect_panel_spec("FRONT", outer_w, front_h)
        specs[front.name] = front

    # Assign finger pair ids to edges and invert flags so mates are complementary.
    # We keep the plan computed for "A" side; panel edges decide whether they are A or B.
    def bind(panel: str, edge: str, pid: str, *, invert: bool):
        spec = specs[panel]
        for e in spec.edges:
            if e.name == edge:
                e.finger_pair_id = pid
                e.invert_tabs = invert
                return
        raise KeyError(f"edge not found: {panel}.{edge}")

    # Bottom/walls
    bind("BOTTOM", "top", "bottom_back", invert=False)
    bind("BACK", "bottom", "bottom_back", invert=True)

    if include_front:
        bind("BOTTOM", "bottom", "bottom_front", invert=False)
        bind("FRONT", "bottom", "bottom_front", invert=True)

    bind("BOTTOM", "left", "bottom_left", invert=False)
    bind("LEFT", "bottom", "bottom_left", invert=True)
    bind("BOTTOM", "right", "bottom_right", invert=False)
    bind("RIGHT", "bottom", "bottom_right", invert=True)

    # Back corners (full height)
    bind("BACK", "left", "corner_back_left", invert=False)
    bind("LEFT", "right", "corner_back_left", invert=True)
    bind("BACK", "right", "corner_back_right", invert=False)
    bind("RIGHT", "left", "corner_back_right", invert=True)

    # Front corners: only if front exists.
    if include_front:
        bind("FRONT", "left", "corner_front_left", invert=False)
        bind("LEFT", "left", "corner_front_left", invert=True)
        bind("FRONT", "right", "corner_front_right", invert=False)
        bind("RIGHT", "right", "corner_front_right", invert=True)

    # Cutouts per preset
    if preset == "window_front":
        specs["FRONT"].cutouts.append(make_window_cutout(outer_w, wall_h * 0.7, margin=p.window_margin, corner_r=p.window_corner_r))
        specs["FRONT"].cutouts.append(make_thumb_notch(outer_w, 0.0, p.thumb_notch_radius, p.thumb_notch_depth))
    elif preset == "dispenser_slot_front":
        # Slot cutout centered in front.
        sw = min(p.slot_width, outer_w - 2 * t)
        sh = min(p.slot_height, wall_h - 2 * t)
        sx = (outer_w - sw) / 2
        sy = max(t, wall_h - p.slot_y_from_bottom - sh)
        specs["FRONT"].cutouts.append(make_rect_cutout(sx, sy, sw, sh))
        specs["FRONT"].cutouts.append(make_thumb_notch(outer_w, 0.0, p.thumb_notch_radius, p.thumb_notch_depth))
    elif preset == "tray_open_front":
        if p.scoop:
            # Scoop cutout in the top edge of the lowered front.
            # This is an internal cutout (notch) to help grabbing cards.
            r = min(p.scoop_radius, outer_w / 2 - t)
            depth = min(p.scoop_depth, front_h - t)
            cx = outer_w / 2
            x0 = cx - r
            x1 = cx + r
            y0 = 0.0
            y1 = depth
            # A simple rounded-U notch.
            d = (
                f"M {fmt(x0)} {fmt(y0)} "
                f"L {fmt(x0)} {fmt(y1)} "
                f"A {fmt(r)} {fmt(r)} 0 0 0 {fmt(x1)} {fmt(y1)} "
                f"L {fmt(x1)} {fmt(y0)} Z"
            )
            specs["FRONT"].cutouts.append(CutPath(d=d))

    # Labels
    if p.labels:
        for s in specs.values():
            s.labels = [(s.name, (s.width / 2, s.height / 2))]

    # Render panels
    panels: List[Panel] = []
    for name in ("BOTTOM", "BACK", "LEFT", "RIGHT"):
        panels.append(render_panel_from_spec(specs[name], joint_params=joint, edge_pairs=edge_pairs))
    if include_front:
        panels.append(render_panel_from_spec(specs["FRONT"], joint_params=joint, edge_pairs=edge_pairs))

    # Lid preset uses additional parts.
    if preset == "box_with_lid" and p.lid:
        c = p.lid_clearance
        lid_in_w = outer_w + 2 * c
        lid_in_d = outer_d + 2 * c
        lid_h = p.lid_height

        lid_specs = [
            build_rect_panel_spec("LID_TOP", lid_in_w, lid_in_d),
            build_rect_panel_spec("LID_BACK", lid_in_w, lid_h),
            build_rect_panel_spec("LID_FRONT", lid_in_w, lid_h),
            build_rect_panel_spec("LID_LEFT", lid_in_d, lid_h),
            build_rect_panel_spec("LID_RIGHT", lid_in_d, lid_h),
        ]
        lid_map = {s.name: s for s in lid_specs}

        # Pairing for lid: treat as a separate box shell with its own edge pairs.
        lid_joint = JointParams(
            thickness=t,
            target_finger_w=target_finger_w,
            min_fingers=p.min_fingers,
            kerf_mm=p.kerf_mm,
            clearance_mm=p.clearance_mm,
            finger_count_outer=p.finger_count_outer,
            finger_count_vertical=p.finger_count_vertical,
        )
        lid_pairs = build_edge_pairs_for_box(
            joint=lid_joint,
            outer_w=lid_in_w,
            outer_d=lid_in_d,
            wall_h=lid_h,
            front_h=lid_h,
            include_front=True,
        )

        def bind_lid(panel: str, edge: str, pid: str, invert: bool):
            spec = lid_map[panel]
            for e in spec.edges:
                if e.name == edge:
                    e.finger_pair_id = pid
                    e.invert_tabs = invert
                    return
            raise KeyError(f"edge not found: {panel}.{edge}")

        # Bottom in this helper is the lid top.
        bind_lid("LID_TOP", "top", "bottom_back", invert=False)
        bind_lid("LID_BACK", "bottom", "bottom_back", invert=True)
        bind_lid("LID_TOP", "bottom", "bottom_front", invert=False)
        bind_lid("LID_FRONT", "bottom", "bottom_front", invert=True)
        bind_lid("LID_TOP", "left", "bottom_left", invert=False)
        bind_lid("LID_LEFT", "bottom", "bottom_left", invert=True)
        bind_lid("LID_TOP", "right", "bottom_right", invert=False)
        bind_lid("LID_RIGHT", "bottom", "bottom_right", invert=True)

        bind_lid("LID_BACK", "left", "corner_back_left", invert=False)
        bind_lid("LID_LEFT", "right", "corner_back_left", invert=True)
        bind_lid("LID_BACK", "right", "corner_back_right", invert=False)
        bind_lid("LID_RIGHT", "left", "corner_back_right", invert=True)
        bind_lid("LID_FRONT", "left", "corner_front_left", invert=False)
        bind_lid("LID_LEFT", "left", "corner_front_left", invert=True)
        bind_lid("LID_FRONT", "right", "corner_front_right", invert=False)
        bind_lid("LID_RIGHT", "right", "corner_front_right", invert=True)

        lid_map["LID_FRONT"].cutouts.append(make_thumb_notch(lid_in_w, 0.0, p.thumb_notch_radius, p.thumb_notch_depth))
        if p.labels:
            for s in lid_map.values():
                s.labels = [(s.name, (s.width / 2, s.height / 2))]

        for nm in ("LID_TOP", "LID_BACK", "LID_FRONT", "LID_LEFT", "LID_RIGHT"):
            panels.append(render_panel_from_spec(lid_map[nm], joint_params=lid_joint, edge_pairs=lid_pairs))
    return panels


def generate_svg_with_warnings(p: BoxParams) -> Tuple[str, List[str]]:
    """Convenience entrypoint for the browser UI.

    Returns:
      (svg_xml, warnings)
    """

    panels = build_panels_for_preset(p)

    # Rebuild edge pairs for warnings (same logic as build_panels_for_preset)
    t = p.thickness
    outer_w = p.inner_width + 2 * t
    outer_d = p.inner_depth + 2 * t
    wall_h = p.inner_height + t
    target_finger_w = p.finger_width if p.finger_width is not None else max(10.0, 3.0 * t)
    joint = JointParams(
        thickness=t,
        target_finger_w=target_finger_w,
        min_fingers=p.min_fingers,
        kerf_mm=p.kerf_mm,
        clearance_mm=p.clearance_mm,
        finger_count_outer=p.finger_count_outer,
        finger_count_vertical=p.finger_count_vertical,
    )
    preset = p.preset
    include_front = preset in ("dispenser_slot_front", "window_front", "tray_open_front", "box_with_lid")
    front_h = p.front_height if p.front_height is not None else wall_h
    if preset == "tray_open_front":
        front_h = p.front_height if p.front_height is not None else max(t * 2, 0.55 * wall_h)
    elif preset in ("dispenser_slot_front", "window_front", "box_with_lid"):
        front_h = wall_h

    edge_pairs = build_edge_pairs_for_box(
        joint=joint,
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
        front_h=front_h,
        include_front=include_front,
    )
    warnings = validate_params_and_pairs(p, edge_pairs)

    meta = p.__dict__.copy()
    meta["joint_rule"] = "drawn_slot = thickness + clearance - kerf (expected final slot ~ thickness + clearance)"
    svg = make_svg(
        panels,
        meta=meta,
        sheet_width=p.sheet_width,
        labels=p.labels,
        offset_kerf=p.offset_kerf,
        kerf_mm=p.kerf_mm,
        layout_margin_mm=p.layout_margin_mm,
        layout_padding_mm=p.layout_padding_mm,
        stroke_mm=p.stroke_mm,
        holding_tabs=p.holding_tabs,
        tab_width_mm=p.tab_width_mm,
    )
    return svg, warnings


def build_calibration_svg(
    *,
    thickness: float,
    kerf_mm: float,
    clearance_values: List[float],
    out_path: str,
    named_presets: Optional[List[Tuple[str, float]]] = None,
):
    """Calibration: generate multiple mating finger-joint strips for different clearances.

    This uses the same primary rule as the main generator:
      drawn_slot = thickness + clearance - kerf
      expected_final_slot ≈ thickness + clearance
    """

    t = thickness
    length = 90.0
    height = 25.0
    gap = 10.0

    joint = JointParams(thickness=t, target_finger_w=max(10.0, 3.0 * t), min_fingers=7, kerf_mm=kerf_mm, clearance_mm=0.0)

    items: List[Tuple[str, float]] = []
    if named_presets:
        items.extend(named_presets)
    items.extend([(f"clr {c:+.2f}", c) for c in clearance_values])

    panels: List[Panel] = []
    y_cursor = 0.0
    for label, c in items:
        joint.clearance_mm = c
        n = compute_finger_count(length, joint.target_finger_w, min_fingers=joint.min_fingers, explicit=None)
        plan = build_finger_plan(length, count=n, kerf_mm=joint.kerf_mm, clearance_mm=joint.clearance_mm, start_with_tab_on_a=True)

        tab_d, slot_d = joint_depths_drawn(thickness=t, kerf_mm=joint.kerf_mm, clearance_mm=c)
        expected_final_slot = t + c

        # Two strips that should mate.
        a_spec = build_rect_panel_spec(f"CAL_A_{label}", length, height)
        b_spec = build_rect_panel_spec(f"CAL_B_{label}", length, height)

        # Use top edge on both as the jointed edge for easy viewing.
        a_spec.edges[0].finger_pair_id = "pair"
        a_spec.edges[0].invert_tabs = False
        b_spec.edges[0].finger_pair_id = "pair"
        b_spec.edges[0].invert_tabs = True

        pair = EdgePair("pair", EdgeFamily.OUTER, EdgeKey(a_spec.name, "top"), EdgeKey(b_spec.name, "top"), length, plan)
        edge_pairs = {"pair": pair}

        a_spec.labels = [
            (
                f"A {label} | drawn slot {slot_d:.2f} | final slot ~ {expected_final_slot:.2f}",
                (length / 2, height / 2),
            )
        ]
        b_spec.labels = [
            (
                f"B {label} | tab {tab_d:.2f}",
                (length / 2, height / 2),
            )
        ]

        a = render_panel_from_spec(a_spec, joint_params=joint, edge_pairs=edge_pairs)
        b = render_panel_from_spec(b_spec, joint_params=joint, edge_pairs=edge_pairs)

        # Translate into a single sheet arrangement (manual).
        a.outline = translate_points(a.outline, 0.0, y_cursor)
        for cut in a.cutouts:
            if cut.points is not None:
                cut.points = translate_points(cut.points, 0.0, y_cursor)
        for i, (txt, (lx, ly)) in enumerate(a.labels):
            a.labels[i] = (txt, (lx, ly + y_cursor))
        panels.append(a)

        b.outline = translate_points(b.outline, length + gap, y_cursor)
        for cut in b.cutouts:
            if cut.points is not None:
                cut.points = translate_points(cut.points, length + gap, y_cursor)
        for i, (txt, (lx, ly)) in enumerate(b.labels):
            b.labels[i] = (txt, (lx + length + gap, ly + y_cursor))
        panels.append(b)

        y_cursor += height + gap

    # Emit as one SVG without layout function.
    width = 2 * length + gap + 20
    height_total = y_cursor + 10
    meta = {"thickness": thickness, "kerf_mm": kerf_mm, "clearances": clearance_values}

    out: List[str] = [svg_header(width, height_total), svg_layer_styles()]
    meta_comment = "\n".join(textwrap.wrap(json.dumps(meta, ensure_ascii=False), width=120))
    out.append(f"  <!-- calibration: {meta_comment} -->\n")
    out.append('  <g id="CUT" class="cut">\n')
    for p in panels:
        out.append(f'    <path d="{polyline_to_path(p.outline, close=True)}"/>\n')
    out.append("  </g>\n")
    out.append('  <g id="ENGRAVE" class="text">\n')
    for p in panels:
        for txt, (tx, ty) in p.labels:
            out.append(f'    <text x="{fmt(tx)}" y="{fmt(ty)}" text-anchor="middle" dominant-baseline="middle">{txt}</text>\n')
    out.append("  </g>\n")
    out.append(svg_footer())

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(out))


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Laser-cut card tray/box generator with deterministic finger-joint pairing.\n\n"
            "Presets: tray_open_front, dispenser_slot_front, window_front, box_with_lid\n"
        ),
    )

    # Back-compat
    ap.add_argument("--variant", default="A", choices=["A", "B", "C"], help="Legacy variant (v0.1).")

    ap.add_argument(
        "--preset",
        default=None,
        choices=["tray_open_front", "dispenser_slot_front", "window_front", "box_with_lid"],
        help="Design preset (preferred).",
    )

    ap.add_argument("--inner-width", type=float, default=70.0)
    ap.add_argument("--inner-depth", type=float, default=95.0)
    ap.add_argument("--inner-height", type=float, default=120.0)
    ap.add_argument("--thickness", type=float, default=3.0)

    # Kerf/fit: keep old flags but add explicit names.
    ap.add_argument("--kerf", type=float, default=0.20, help="Alias for --kerf-mm")
    ap.add_argument("--kerf-mm", type=float, default=None, help="Laser kerf (e.g. 0.15–0.25)")
    ap.add_argument("--fit", type=float, default=0.15, help="Legacy alias for --clearance-mm")
    ap.add_argument("--clearance", type=float, default=None, help="Alias for --clearance-mm")
    ap.add_argument("--clearance-mm", type=float, default=None, help="Target slot-tab clearance (+looser)")

    ap.add_argument("--finger-width", type=float, default=None, help="Target finger width (mm)")
    ap.add_argument("--min-fingers", type=int, default=3)
    ap.add_argument("--finger-count-outer", type=int, default=None, help="Optional explicit finger count for OUTER joints")
    ap.add_argument("--finger-count-vertical", type=int, default=None, help="Optional explicit finger count for VERTICAL joints")

    # Lid
    ap.add_argument("--no-lid", action="store_true")
    ap.add_argument("--lid-height", type=float, default=25.0)
    ap.add_argument("--lid-clearance", type=float, default=0.4)

    # Preset params
    ap.add_argument("--front-height", type=float, default=None, help="Front wall height (tray_open_front)")
    ap.add_argument("--scoop", action="store_true", help="Add scoop cutout on lowered front")
    ap.add_argument("--scoop-radius", type=float, default=22.0)
    ap.add_argument("--scoop-depth", type=float, default=18.0)

    ap.add_argument("--slot-width", type=float, default=80.0)
    ap.add_argument("--slot-height", type=float, default=18.0)
    ap.add_argument("--slot-y-from-bottom", type=float, default=35.0)

    ap.add_argument("--window-margin", type=float, default=18.0)
    ap.add_argument("--window-corner-r", type=float, default=6.0)
    ap.add_argument("--thumb-notch-radius", type=float, default=10.0)
    ap.add_argument("--thumb-notch-depth", type=float, default=8.0)

    ap.add_argument("--sheet-width", type=float, default=320.0, help="Layout wrap width (mm)")
    ap.add_argument("--margin-mm", type=float, default=10.0, help="Outer layout margin (mm)")
    ap.add_argument("--padding-mm", type=float, default=12.0, help="Spacing between parts in layout (mm)")
    ap.add_argument("--stroke-mm", type=float, default=0.2, help="SVG stroke width for CUT/SCORE/ENGRAVE (mm)")
    ap.add_argument("--export", choices=["single_svg", "per_panel_svgs"], default="single_svg")
    ap.add_argument("--offset-kerf", action="store_true", help="If pyclipper is installed, offset cut paths by kerf/2")
    ap.add_argument("--holding-tabs", action="store_true", help="Leave small uncut gaps (bridges) on polygon cuts")
    ap.add_argument("--tab-width", type=float, default=2.0, help="Holding tab width (mm), default 2.0")

    ap.add_argument("--no-labels", action="store_true")
    ap.add_argument("--out", required=True, help="Output path (single SVG) or directory (per_panel_svgs)")

    ap.add_argument("--calibration", action="store_true", help="Generate calibration plate (mating strips)")
    ap.add_argument(
        "--calibration-set",
        choices=["full", "student"],
        default="full",
        help="Calibration clearances set: full (many values) or student (tight/normal/loose)",
    )
    ap.add_argument(
        "--calibration-clearances",
        type=str,
        default="-0.10,-0.05,0,0.05,0.10,0.15,0.20",
        help="Comma-separated clearance values for calibration",
    )
    return ap.parse_args()


def main():
    args = parse_args()

    kerf_mm = args.kerf_mm if args.kerf_mm is not None else float(args.kerf)
    if args.clearance_mm is not None:
        clearance_mm = float(args.clearance_mm)
    elif args.clearance is not None:
        clearance_mm = float(args.clearance)
    else:
        clearance_mm = float(args.fit)

    if args.calibration:
        named = None
        if args.calibration_set == "student":
            named = [("tight", 0.00), ("normal", 0.10), ("loose", 0.20)]
        clearances = [float(x) for x in args.calibration_clearances.split(",") if x.strip() != ""]
        build_calibration_svg(
            thickness=args.thickness,
            kerf_mm=kerf_mm,
            clearance_values=clearances,
            out_path=args.out,
            named_presets=named,
        )
        return

    # Map legacy variants to presets.
    preset = args.preset
    if preset is None:
        if args.variant.upper() == "A":
            preset = "tray_open_front"
        elif args.variant.upper() == "B":
            preset = "window_front"
        else:
            preset = "box_with_lid"

    p = BoxParams(
        variant=args.variant,
        preset=preset,
        inner_width=args.inner_width,
        inner_depth=args.inner_depth,
        inner_height=args.inner_height,
        thickness=args.thickness,
        kerf_mm=kerf_mm,
        clearance_mm=clearance_mm,
        finger_width=args.finger_width,
        min_fingers=args.min_fingers,
        finger_count_outer=args.finger_count_outer,
        finger_count_vertical=args.finger_count_vertical,
        lid=not args.no_lid,
        lid_height=args.lid_height,
        lid_clearance=args.lid_clearance,
        front_height=args.front_height,
        scoop=args.scoop,
        scoop_radius=args.scoop_radius,
        scoop_depth=args.scoop_depth,
        slot_width=args.slot_width,
        slot_height=args.slot_height,
        slot_y_from_bottom=args.slot_y_from_bottom,
        window_margin=args.window_margin,
        window_corner_r=args.window_corner_r,
        thumb_notch_radius=args.thumb_notch_radius,
        thumb_notch_depth=args.thumb_notch_depth,
        labels=not args.no_labels,
        sheet_width=args.sheet_width,
        layout_margin_mm=args.margin_mm,
        layout_padding_mm=args.padding_mm,
        stroke_mm=args.stroke_mm,
        export=args.export,
        offset_kerf=args.offset_kerf,
        holding_tabs=args.holding_tabs,
        tab_width_mm=args.tab_width,
    )

    panels = build_panels_for_preset(p)
    # Basic invariants
    for panel in panels:
        if len(panel.outline) < 4 or abs(polygon_area(panel.outline)) < 1e-6:
            raise RuntimeError(f"Degenerate panel outline: {panel.name}")

    meta = p.__dict__.copy()
    meta["note"] = "Generated by deterministic edge-pair cardboxgen"

    if p.export == "single_svg":
        svg = make_svg(
            panels,
            meta=meta,
            sheet_width=p.sheet_width,
            labels=p.labels,
            offset_kerf=p.offset_kerf,
            kerf_mm=p.kerf_mm,
            layout_margin_mm=p.layout_margin_mm,
            layout_padding_mm=p.layout_padding_mm,
            stroke_mm=p.stroke_mm,
            holding_tabs=p.holding_tabs,
            tab_width_mm=p.tab_width_mm,
        )
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(svg)
        return

    # per_panel_svgs
    import os

    os.makedirs(args.out, exist_ok=True)
    for panel in panels:
        svg = make_svg(
            [panel],
            meta={**meta, "single_panel": panel.name},
            sheet_width=max(panel.bbox()[0] + 20, 50),
            labels=p.labels,
            offset_kerf=p.offset_kerf,
            kerf_mm=p.kerf_mm,
            layout_margin_mm=p.layout_margin_mm,
            layout_padding_mm=p.layout_padding_mm,
            stroke_mm=p.stroke_mm,
            holding_tabs=p.holding_tabs,
            tab_width_mm=p.tab_width_mm,
        )
        out_path = os.path.join(args.out, f"{panel.name}.svg")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)


if __name__ == "__main__":
    main()
