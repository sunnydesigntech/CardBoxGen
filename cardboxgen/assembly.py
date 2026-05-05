"""Explicit assembly graph primitives for mechanically paired panels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .joints import EdgeFamily, EdgeKey, build_finger_plan, compute_finger_count
from .panels import EdgePair, EdgeRole, PanelEdge, PanelSpec, bind_edge


@dataclass(frozen=True)
class EdgeRef:
    panel: str
    edge: str

    def key(self) -> Tuple[str, str]:
        return (self.panel, self.edge)

    def to_edge_key(self) -> EdgeKey:
        return EdgeKey(self.panel, self.edge)


@dataclass(frozen=True)
class EdgeBinding:
    pair_id: str
    ref: EdgeRef
    role: str
    invert_tabs: bool
    reverse_plan: bool = False
    offset_start: float = 0.0
    offset_end: float = 0.0


@dataclass(frozen=True)
class JointPairSpec:
    id: str
    family: str
    a: EdgeBinding
    b: EdgeBinding
    length: float
    start_with_tab_on_a: bool = True
    explicit_count: Optional[int] = None


@dataclass
class AssemblyGraph:
    """Nominal graph tying panel edges to shared finger plans."""

    panels: Dict[str, PanelSpec]
    joint_specs: List[JointPairSpec]
    edge_pairs: Dict[str, EdgePair] = field(default_factory=dict)
    bindings: Dict[Tuple[str, str], EdgeBinding] = field(default_factory=dict)

    def compile(
        self,
        *,
        target_finger_w: float,
        min_fingers: int,
        kerf: float,
        clearance: float,
    ) -> None:
        self.edge_pairs = {}
        self.bindings = {}
        for joint in self.joint_specs:
            self._register_binding(joint.a)
            self._register_binding(joint.b)
            count = compute_finger_count(
                joint.length,
                target_finger_w,
                min_fingers=min_fingers,
                explicit=joint.explicit_count,
            )
            plan = build_finger_plan(
                joint.length,
                count=count,
                kerf_mm=kerf,
                clearance_mm=clearance,
                start_with_tab_on_a=joint.start_with_tab_on_a,
            )
            self.edge_pairs[joint.id] = EdgePair(
                id=joint.id,
                family=joint.family,
                a=joint.a.ref.to_edge_key(),
                b=joint.b.ref.to_edge_key(),
                length=joint.length,
                plan=plan,
                role_a=joint.a.role,
                role_b=joint.b.role,
                reverse_a=joint.a.reverse_plan,
                reverse_b=joint.b.reverse_plan,
            )

        self.validate()
        for joint in self.joint_specs:
            self._bind(joint.a)
            self._bind(joint.b)

    def _register_binding(self, binding: EdgeBinding) -> None:
        key = binding.ref.key()
        if key in self.bindings:
            raise ValueError(f"assembly edge has more than one partner: {binding.ref.panel}.{binding.ref.edge}")
        self.bindings[key] = binding

    def _bind(self, binding: EdgeBinding) -> None:
        bind_edge(
            self.panels,
            binding.ref.panel,
            binding.ref.edge,
            binding.pair_id,
            invert=binding.invert_tabs,
            reverse=binding.reverse_plan,
            role=binding.role,
            offset_start=binding.offset_start,
            offset_end=binding.offset_end,
        )

    def validate(self) -> None:
        for joint in self.joint_specs:
            if joint.length <= 0:
                raise ValueError(f"joint length must be positive: {joint.id}")
            for binding in (joint.a, joint.b):
                panel = self.panels.get(binding.ref.panel)
                if panel is None:
                    raise ValueError(f"unknown panel in assembly graph: {binding.ref.panel}")
                edge = _find_edge(panel, binding.ref.edge)
                available = edge.length - binding.offset_start - binding.offset_end
                if available + 1e-9 < joint.length:
                    raise ValueError(
                        f"joint {joint.id} is longer than {binding.ref.panel}.{binding.ref.edge}: "
                        f"{joint.length:.3f} > {available:.3f}"
                    )
            if joint.a.role == EdgeRole.FLAT or joint.b.role == EdgeRole.FLAT:
                raise ValueError(f"mating edge is accidentally flat: {joint.id}")

    def panel_edge_meta(self) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for panel in self.panels.values():
            edge_items: List[Dict[str, object]] = []
            for edge in panel.edges:
                edge_items.append(
                    {
                        "id": edge.name,
                        "role": edge.role,
                        "length": edge.length,
                        "start": [edge.start[0], edge.start[1]],
                        "dir": [edge.dirv[0], edge.dirv[1]],
                        "joint_pair_id": edge.finger_pair_id,
                        "reverse_plan": edge.reverse_plan,
                        "invert_tabs": edge.invert_tabs,
                        "offset_start": edge.joint_offset_start,
                        "offset_end": edge.joint_offset_end,
                    }
                )
            out.append({"id": panel.name, "width": panel.width, "height": panel.height, "edges": edge_items})
        return out


def make_box_panel_specs(
    *,
    outer_w: float,
    outer_d: float,
    wall_h: float,
    front_panel_h: float,
    include_front: bool,
    prefix: str = "",
) -> Dict[str, PanelSpec]:
    def name(part: str) -> str:
        return f"{prefix}{part}" if prefix else part

    specs: Dict[str, PanelSpec] = {
        name("BOTTOM"): _rect_spec(
            name("BOTTOM"),
            outer_w,
            outer_d,
            ("back", "right", "front", "left"),
        ),
        name("BACK"): _rect_spec(
            name("BACK"),
            outer_w,
            wall_h,
            ("top", "right", "bottom", "left"),
        ),
        # Side panels use a consistent local x-axis from front to back.
        name("LEFT"): _rect_spec(
            name("LEFT"),
            outer_d,
            wall_h,
            ("top", "back", "bottom", "front"),
        ),
        name("RIGHT"): _rect_spec(
            name("RIGHT"),
            outer_d,
            wall_h,
            ("top", "back", "bottom", "front"),
        ),
    }
    if include_front:
        specs[name("FRONT")] = _rect_spec(
            name("FRONT"),
            outer_w,
            front_panel_h,
            ("top", "right", "bottom", "left"),
        )
    return specs


def make_rectangular_box_graph(
    *,
    outer_w: float,
    outer_d: float,
    wall_h: float,
    front_panel_h: float,
    include_front: bool,
    prefix: str = "",
    joint_margin: float = 0.0,
    finger_count_outer: Optional[int] = None,
    finger_count_vertical: Optional[int] = None,
) -> AssemblyGraph:
    specs = make_box_panel_specs(
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
        front_panel_h=front_panel_h,
        include_front=include_front,
        prefix=prefix,
    )

    def name(part: str) -> str:
        return f"{prefix}{part}" if prefix else part

    def ref(panel: str, edge: str) -> EdgeRef:
        return EdgeRef(name(panel), edge)

    margin = max(0.0, float(joint_margin))
    full_w = max(0.1, outer_w - 2 * margin)
    full_d = max(0.1, outer_d - 2 * margin)
    full_h = max(0.1, wall_h - 2 * margin)
    front_h = max(0.1, front_panel_h - 2 * margin)

    def binding(
        pair_id: str,
        panel: str,
        edge: str,
        *,
        invert: bool,
        reverse: bool = False,
        offset_start: float = 0.0,
        offset_end: float = 0.0,
    ) -> EdgeBinding:
        panel_name = name(panel)
        return EdgeBinding(
            pair_id=pair_id,
            ref=ref(panel, edge),
            role=EdgeRole.SLOTTED if invert else EdgeRole.TABBED,
            invert_tabs=invert,
            reverse_plan=reverse,
            offset_start=max(0.0, offset_start),
            offset_end=max(0.0, offset_end),
        )

    joints: List[JointPairSpec] = [
        _pair(
            f"{prefix}bottom_back",
            EdgeFamily.OUTER,
            binding(f"{prefix}bottom_back", "BOTTOM", "back", invert=False, offset_start=margin, offset_end=margin),
            binding(f"{prefix}bottom_back", "BACK", "bottom", invert=True, reverse=True, offset_start=margin, offset_end=margin),
            full_w,
            finger_count_outer,
        ),
        _pair(
            f"{prefix}bottom_left",
            EdgeFamily.OUTER,
            binding(f"{prefix}bottom_left", "BOTTOM", "left", invert=False, offset_start=margin, offset_end=margin),
            binding(f"{prefix}bottom_left", "LEFT", "bottom", invert=True, reverse=True, offset_start=margin, offset_end=margin),
            full_d,
            finger_count_outer,
        ),
        _pair(
            f"{prefix}bottom_right",
            EdgeFamily.OUTER,
            binding(f"{prefix}bottom_right", "BOTTOM", "right", invert=False, offset_start=margin, offset_end=margin),
            binding(f"{prefix}bottom_right", "RIGHT", "bottom", invert=True, offset_start=margin, offset_end=margin),
            full_d,
            finger_count_outer,
        ),
        _pair(
            f"{prefix}corner_back_left",
            EdgeFamily.VERTICAL,
            binding(f"{prefix}corner_back_left", "BACK", "left", invert=False, offset_start=margin, offset_end=margin),
            binding(f"{prefix}corner_back_left", "LEFT", "back", invert=True, reverse=True, offset_start=margin, offset_end=margin),
            full_h,
            finger_count_vertical,
        ),
        _pair(
            f"{prefix}corner_back_right",
            EdgeFamily.VERTICAL,
            binding(f"{prefix}corner_back_right", "BACK", "right", invert=False, offset_start=margin, offset_end=margin),
            binding(f"{prefix}corner_back_right", "RIGHT", "back", invert=True, offset_start=margin, offset_end=margin),
            full_h,
            finger_count_vertical,
        ),
    ]

    if include_front:
        joints.extend(
            [
                _pair(
                    f"{prefix}bottom_front",
                    EdgeFamily.OUTER,
                    binding(f"{prefix}bottom_front", "BOTTOM", "front", invert=False, offset_start=margin, offset_end=margin),
                    binding(f"{prefix}bottom_front", "FRONT", "bottom", invert=True, offset_start=margin, offset_end=margin),
                    full_w,
                    finger_count_outer,
                ),
                _pair(
                    f"{prefix}corner_front_left",
                    EdgeFamily.VERTICAL,
                    binding(f"{prefix}corner_front_left", "FRONT", "left", invert=False, offset_start=margin, offset_end=margin),
                    binding(
                        f"{prefix}corner_front_left",
                        "LEFT",
                        "front",
                        invert=True,
                        offset_start=margin,
                        offset_end=max(0.0, wall_h - front_panel_h + margin),
                    ),
                    front_h,
                    finger_count_vertical,
                ),
                _pair(
                    f"{prefix}corner_front_right",
                    EdgeFamily.VERTICAL,
                    binding(f"{prefix}corner_front_right", "FRONT", "right", invert=False, reverse=True, offset_start=margin, offset_end=margin),
                    binding(
                        f"{prefix}corner_front_right",
                        "RIGHT",
                        "front",
                        invert=True,
                        offset_start=margin,
                        offset_end=max(0.0, wall_h - front_panel_h + margin),
                    ),
                    front_h,
                    finger_count_vertical,
                ),
            ]
        )

    return AssemblyGraph(panels=specs, joint_specs=joints)


def _pair(
    pair_id: str,
    family: str,
    a: EdgeBinding,
    b: EdgeBinding,
    length: float,
    explicit_count: Optional[int],
) -> JointPairSpec:
    return JointPairSpec(
        id=pair_id,
        family=family,
        a=a,
        b=b,
        length=float(length),
        explicit_count=explicit_count,
    )


def _rect_spec(name: str, w: float, h: float, edge_names: Tuple[str, str, str, str]) -> PanelSpec:
    p0 = (0.0, 0.0)
    p1 = (w, 0.0)
    p2 = (w, h)
    p3 = (0.0, h)
    return PanelSpec(
        name=name,
        width=w,
        height=h,
        edges=[
            PanelEdge(edge_names[0], start=p0, dirv=(1, 0), length=w),
            PanelEdge(edge_names[1], start=p1, dirv=(0, 1), length=h),
            PanelEdge(edge_names[2], start=p2, dirv=(-1, 0), length=w),
            PanelEdge(edge_names[3], start=p3, dirv=(0, -1), length=h),
        ],
    )


def _find_edge(panel: PanelSpec, edge_name: str) -> PanelEdge:
    for edge in panel.edges:
        if edge.name == edge_name:
            return edge
    raise KeyError(f"edge not found: {panel.name}.{edge_name}")
