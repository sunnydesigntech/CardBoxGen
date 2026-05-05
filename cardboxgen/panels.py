"""Panel and cut path primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .geometry import Point, add, bbox_points, mul, outward_normal_for_edge, polygon_area, polyline_to_path
from .fabrication import final_segment_widths
from .joints import EdgeKey, FingerPlan, joint_depths_drawn


class EdgeRole:
    FLAT = "flat"
    TABBED = "tabbed"
    SLOTTED = "slotted"
    OPEN = "open"
    SCORE = "score"


class CornerPolicy:
    RESERVED_NO_FINGER_ZONE = "reserved_no_finger_zone"
    CLEAN_SQUARE = "clean_square"


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
class EdgeProfile:
    """Local edge polyline. Points must start at (0, 0) and end at (length, 0)."""

    length: float
    role: str
    points: List[Point]
    corner_clearance_start: float = 0.0
    corner_clearance_end: float = 0.0
    finger_plan_id: Optional[str] = None
    transition_xs: List[float] = field(default_factory=list)

    def validate(self) -> None:
        if self.length <= 0:
            raise ValueError("edge profile length must be positive")
        if not self.points:
            raise ValueError("edge profile has no points")
        if _dist2(self.points[0], (0.0, 0.0)) > 1e-12:
            raise ValueError("edge profile must start at (0, 0)")
        if _dist2(self.points[-1], (self.length, 0.0)) > 1e-12:
            raise ValueError("edge profile must end at (length, 0)")
        for x, _y in self.points:
            if x < -1e-9 or x > self.length + 1e-9:
                raise ValueError("edge profile point is outside local x range")
        for a, b in zip(self.points, self.points[1:]):
            if _dist2(a, b) <= 1e-18:
                raise ValueError("edge profile contains a zero-length segment")
        for x in self.transition_xs:
            if x < self.corner_clearance_start - 1e-9:
                raise ValueError("finger transition starts inside reserved corner clearance")
            if x > self.length - self.corner_clearance_end + 1e-9:
                raise ValueError("finger transition ends inside reserved corner clearance")


@dataclass
class PanelOutline:
    panel_id: str
    nominal_width: float
    nominal_height: float
    edges: Dict[str, EdgeProfile]
    corners: Dict[str, str] = field(default_factory=dict)


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
    outline = build_panel_outline(spec, joint_params=joint_params, edge_pairs=edge_pairs)
    pts = compose_panel_outline(spec, outline)

    return Panel(
        name=spec.name,
        outline=pts,
        cutouts=list(spec.cutouts),
        score_paths=list(spec.score_paths),
        labels=list(spec.labels),
        notes=list(spec.notes),
    )


def build_panel_outline(spec: PanelSpec, *, joint_params: JointRenderParams, edge_pairs: Dict[str, EdgePair]) -> PanelOutline:
    profiles: Dict[str, EdgeProfile] = {}
    for edge in spec.edges:
        profiles[edge.name] = edge_profile_from_panel_edge(edge, joint_params=joint_params, edge_pairs=edge_pairs)
    return PanelOutline(
        panel_id=spec.name,
        nominal_width=spec.width,
        nominal_height=spec.height,
        edges=profiles,
        corners={
            "top_right": CornerPolicy.RESERVED_NO_FINGER_ZONE,
            "bottom_right": CornerPolicy.RESERVED_NO_FINGER_ZONE,
            "bottom_left": CornerPolicy.RESERVED_NO_FINGER_ZONE,
            "top_left": CornerPolicy.RESERVED_NO_FINGER_ZONE,
        },
    )


def edge_profile_from_panel_edge(edge: PanelEdge, *, joint_params: JointRenderParams, edge_pairs: Dict[str, EdgePair]) -> EdgeProfile:
    if edge.finger_pair_id is None:
        profile = EdgeProfile(length=edge.length, role=edge.role, points=[(0.0, 0.0), (edge.length, 0.0)])
        profile.validate()
        return profile

    pair = edge_pairs[edge.finger_pair_id]
    profile = make_finger_edge_profile(
        length=edge.length,
        plan=pair.plan,
        role=edge.role,
        thickness=joint_params.thickness,
        kerf_mm=joint_params.kerf_mm,
        clearance_mm=joint_params.clearance_mm,
        invert_tabs=edge.invert_tabs,
        reverse_plan=edge.reverse_plan,
        corner_clearance_start=edge.joint_offset_start,
        corner_clearance_end=edge.joint_offset_end,
        finger_plan_id=edge.finger_pair_id,
    )
    profile.validate()
    return profile


def make_finger_edge_profile(
    *,
    length: float,
    plan: FingerPlan,
    role: str,
    thickness: float,
    kerf_mm: float,
    clearance_mm: float,
    invert_tabs: bool,
    reverse_plan: bool = False,
    corner_clearance_start: float = 0.0,
    corner_clearance_end: float = 0.0,
    finger_plan_id: Optional[str] = None,
) -> EdgeProfile:
    """Create a local, corner-free edge profile from x=0 to x=length."""

    edge_len = float(length)
    start_clear = max(0.0, float(corner_clearance_start))
    end_clear = max(0.0, float(corner_clearance_end))
    usable = edge_len - start_clear - end_clear
    if usable + 1e-9 < plan.length:
        raise ValueError(f"finger plan length {plan.length:.3f} exceeds usable edge span {usable:.3f}")

    tab_depth, slot_depth = joint_depths_drawn(thickness=thickness, kerf_mm=kerf_mm, clearance_mm=clearance_mm)
    mask = plan.local_tabs_mask(invert=invert_tabs, reverse=reverse_plan)
    widths = plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=invert_tabs, reverse=reverse_plan)

    points: List[Point] = [(0.0, 0.0)]
    if start_clear > 0:
        points.append((start_clear, 0.0))

    x = start_clear
    transition_xs: List[float] = []
    for width, is_tab in zip(widths, mask):
        width = float(width)
        depth = tab_depth if is_tab else slot_depth
        y = depth if is_tab else -depth
        x2 = x + width
        points.extend([(x, y), (x2, y), (x2, 0.0)])
        transition_xs.extend([x, x2])
        x = x2

    usable_end = start_clear + plan.length
    if abs(x - usable_end) > 1e-6:
        raise ValueError("finger profile did not end at expected usable span")
    if usable_end < edge_len - 1e-9:
        points.append((edge_len, 0.0))

    compact = _compact_points(points)
    profile = EdgeProfile(
        length=edge_len,
        role=role,
        points=compact,
        corner_clearance_start=start_clear,
        corner_clearance_end=end_clear,
        finger_plan_id=finger_plan_id,
        transition_xs=transition_xs,
    )
    profile.validate()
    return profile


def compose_panel_outline(spec: PanelSpec, outline: PanelOutline) -> List[Point]:
    """Transform local edge profiles and connect corners exactly once."""

    pts: List[Point] = []
    for edge in spec.edges:
        profile = outline.edges[edge.name]
        profile.validate()
        normal = outward_normal_for_edge(edge.dirv)
        transformed = [add(add(edge.start, mul(edge.dirv, x)), mul(normal, y)) for x, y in profile.points]
        for point in transformed:
            if pts and _dist2(point, pts[-1]) <= 1e-18:
                continue
            pts.append(point)
    if len(pts) > 1 and _dist2(pts[0], pts[-1]) <= 1e-18:
        pts.pop()
    return pts


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


def _dist2(a: Point, b: Point) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _compact_points(points: List[Point]) -> List[Point]:
    compact: List[Point] = []
    for point in points:
        if compact and _dist2(point, compact[-1]) <= 1e-18:
            continue
        compact.append(point)
    return compact
