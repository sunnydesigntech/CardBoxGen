"""Panel and cut path primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .geometry import Point, add, bbox_points, mul, outward_normal_for_edge, polygon_area, polyline_to_path
from .fabrication import final_segment_widths
from .joints import EdgeKey, FingerPlan, finger_edge_points


class EdgeRole:
    FLAT = "flat"
    TABBED = "tabbed"
    SLOTTED = "slotted"
    OPEN = "open"
    SCORE = "score"


@dataclass
class CutPath:
    """A separate laser cut path on the CUT layer."""

    points: Optional[List[Point]] = None
    d: Optional[str] = None
    kind: str = "cutout"
    bbox_hint: Optional[Tuple[float, float, float, float]] = None

    def to_svg_d(self) -> str:
        if self.d is not None:
            return self.d
        if self.points is None:
            return ""
        return polyline_to_path(self.points, close=True)

    def bbox(self) -> Optional[Tuple[float, float, float, float]]:
        if self.bbox_hint is not None:
            return self.bbox_hint
        if self.points:
            return bbox_points(self.points)
        return None


@dataclass
class Panel:
    name: str
    outline: List[Point]
    cutouts: List[CutPath] = field(default_factory=list)
    score_paths: List[CutPath] = field(default_factory=list)
    labels: List[Tuple[str, Point]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def bbox(self) -> Tuple[float, float, float, float]:
        return bbox_points(self.outline)

    def bbox_size(self) -> Point:
        x0, y0, x1, y1 = self.bbox()
        return (x1 - x0, y1 - y0)

    def area(self) -> float:
        return polygon_area(self.outline)


@dataclass
class EdgePair:
    id: str
    family: str
    a: EdgeKey
    b: EdgeKey
    length: float
    plan: FingerPlan
    role_a: str = EdgeRole.TABBED
    role_b: str = EdgeRole.SLOTTED
    reverse_a: bool = False
    reverse_b: bool = False

    def to_meta(self, *, thickness: float | None = None, kerf_mm: float | None = None, clearance_mm: float | None = None) -> Dict[str, object]:
        tabs_a_local = self.plan.local_tabs_mask(invert=False, reverse=self.reverse_a)
        tabs_b_local = self.plan.local_tabs_mask(invert=True, reverse=self.reverse_b)
        data: Dict[str, object] = {
            "id": self.id,
            "family": self.family,
            "finger_plan_id": self.id,
            "a": {"panel": self.a.panel, "edge": self.a.edge, "role": self.role_a, "reverse": self.reverse_a},
            "b": {"panel": self.b.panel, "edge": self.b.edge, "role": self.role_b, "reverse": self.reverse_b},
            "length": self.length,
            "count": self.plan.count,
            "widths": list(self.plan.widths),
            "tabs_a": self.plan.tabs_mask_for_a(),
            "tabs_b": self.plan.complement_mask(),
            "tabs_a_local": tabs_a_local,
            "tabs_b_local": tabs_b_local,
            "nominal_boundaries": _boundaries(self.plan.widths),
        }
        if kerf_mm is not None and clearance_mm is not None:
            drawn_a = self.plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=False)
            drawn_b = self.plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=True)
            drawn_a_local = self.plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=False, reverse=self.reverse_a)
            drawn_b_local = self.plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=True, reverse=self.reverse_b)
            data.update(
                {
                    "drawn_widths_a": drawn_a,
                    "drawn_widths_b": drawn_b,
                    "drawn_widths_a_local": drawn_a_local,
                    "drawn_widths_b_local": drawn_b_local,
                    "final_widths_a": final_segment_widths(drawn_a, self.plan.tabs_mask_for_a(), kerf_full_width_mm=kerf_mm),
                    "final_widths_b": final_segment_widths(drawn_b, self.plan.complement_mask(), kerf_full_width_mm=kerf_mm),
                    "drawn_boundaries_a": _boundaries(drawn_a),
                    "drawn_boundaries_b": _boundaries(drawn_b),
                    "drawn_boundaries_a_local": _boundaries(drawn_a_local),
                    "drawn_boundaries_b_local": _boundaries(drawn_b_local),
                    "target_clearance": clearance_mm,
                    "thickness": thickness,
                    "kerf_full_width_mm": kerf_mm,
                }
            )
        return data


@dataclass
class PanelEdge:
    name: str
    start: Point
    dirv: Point
    length: float
    finger_pair_id: Optional[str] = None
    invert_tabs: bool = False
    reverse_plan: bool = False
    role: str = EdgeRole.FLAT
    joint_offset_start: float = 0.0
    joint_offset_end: float = 0.0


@dataclass
class PanelSpec:
    name: str
    width: float
    height: float
    edges: List[PanelEdge]
    cutouts: List[CutPath] = field(default_factory=list)
    score_paths: List[CutPath] = field(default_factory=list)
    labels: List[Tuple[str, Point]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class JointRenderParams:
    thickness: float
    kerf_mm: float
    clearance_mm: float


def build_rect_panel_spec(name: str, w: float, h: float) -> PanelSpec:
    p0 = (0.0, 0.0)
    p1 = (w, 0.0)
    p2 = (w, h)
    p3 = (0.0, h)
    return PanelSpec(
        name=name,
        width=w,
        height=h,
        edges=[
            PanelEdge("top", start=p0, dirv=(1, 0), length=w),
            PanelEdge("right", start=p1, dirv=(0, 1), length=h),
            PanelEdge("bottom", start=p2, dirv=(-1, 0), length=w),
            PanelEdge("left", start=p3, dirv=(0, -1), length=h),
        ],
    )


def render_panel_from_spec(spec: PanelSpec, *, joint_params: JointRenderParams, edge_pairs: Dict[str, EdgePair]) -> Panel:
    pts: List[Point] = [spec.edges[0].start]
    for edge in spec.edges:
        start = edge.start
        dirv = edge.dirv
        normal = outward_normal_for_edge(dirv)
        if edge.finger_pair_id is None:
            pts.append(add(start, mul(dirv, edge.length)))
            continue

        pair = edge_pairs[edge.finger_pair_id]
        if edge.joint_offset_start > 0:
            start = add(start, mul(dirv, edge.joint_offset_start))
            pts.append(start)
        pts.extend(
            finger_edge_points(
                start,
                dirv,
                normal,
                pair.plan,
                thickness=joint_params.thickness,
                kerf_mm=joint_params.kerf_mm,
                clearance_mm=joint_params.clearance_mm,
                invert_tabs=edge.invert_tabs,
                reverse_plan=edge.reverse_plan,
            )
        )
        endpoint = add(edge.start, mul(dirv, edge.length))
        if pair.plan.length + edge.joint_offset_start < edge.length - 1e-9:
            pts.append(endpoint)

    compact: List[Point] = []
    for point in pts:
        if not compact or abs(point[0] - compact[-1][0]) > 1e-9 or abs(point[1] - compact[-1][1]) > 1e-9:
            compact.append(point)

    return Panel(
        name=spec.name,
        outline=compact,
        cutouts=list(spec.cutouts),
        score_paths=list(spec.score_paths),
        labels=list(spec.labels),
        notes=list(spec.notes),
    )


def bind_edge(
    specs: Dict[str, PanelSpec],
    panel: str,
    edge: str,
    pair_id: str,
    *,
    invert: bool,
    reverse: bool = False,
    role: str | None = None,
    offset_start: float = 0.0,
    offset_end: float = 0.0,
) -> None:
    for item in specs[panel].edges:
        if item.name == edge:
            item.finger_pair_id = pair_id
            item.invert_tabs = invert
            item.reverse_plan = reverse
            item.role = role or (EdgeRole.SLOTTED if invert else EdgeRole.TABBED)
            item.joint_offset_start = max(0.0, float(offset_start))
            item.joint_offset_end = max(0.0, float(offset_end))
            return
    raise KeyError(f"edge not found: {panel}.{edge}")


def _boundaries(widths: List[float]) -> List[float]:
    out = [0.0]
    acc = 0.0
    for width in widths:
        acc += float(width)
        out.append(acc)
    if out:
        out[-1] = round(out[-1], 12)
    return out
