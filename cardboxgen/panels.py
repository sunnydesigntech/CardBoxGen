"""Panel and cut path primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .geometry import Point, add, bbox_points, mul, outward_normal_for_edge, polygon_area, polyline_to_path
from .joints import EdgeKey, FingerPlan, finger_edge_points


@dataclass
class CutPath:
    """A separate laser cut path on the CUT layer."""

    points: Optional[List[Point]] = None
    d: Optional[str] = None
    kind: str = "cutout"

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

    def to_meta(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "family": self.family,
            "a": {"panel": self.a.panel, "edge": self.a.edge},
            "b": {"panel": self.b.panel, "edge": self.b.edge},
            "length": self.length,
            "count": self.plan.count,
            "widths": list(self.plan.widths),
            "tabs_a": self.plan.tabs_mask_for_a(),
            "tabs_b": self.plan.complement_mask(),
        }


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
            )
        )
        if pair.plan.length < edge.length - 1e-9:
            pts.append(add(start, mul(dirv, edge.length)))

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


def bind_edge(specs: Dict[str, PanelSpec], panel: str, edge: str, pair_id: str, *, invert: bool) -> None:
    for item in specs[panel].edges:
        if item.name == edge:
            item.finger_pair_id = pair_id
            item.invert_tabs = invert
            return
    raise KeyError(f"edge not found: {panel}.{edge}")
