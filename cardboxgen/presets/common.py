"""Shared preset construction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..assembly import make_rectangular_box_graph
from ..geometry import circle_path, rect_path, rounded_rect_path, thumb_notch_path
from ..joints import EdgeFamily, EdgeKey, build_finger_plan, compute_finger_count, joint_depths_drawn
from ..models import WarningMsg
from ..panels import CutPath, EdgePair, JointRenderParams, Panel, PanelSpec, bind_edge, build_rect_panel_spec, render_panel_from_spec


@dataclass
class BoxBuild:
    panels: List[Panel]
    warnings: List[WarningMsg]
    meta: Dict[str, object]
    edge_pairs: Dict[str, EdgePair]
    specs: Dict[str, PanelSpec]
    outer_w: float
    outer_d: float
    wall_h: float
    front_panel_h: float


def warn(severity: str, code: str, message: str, fix: str = "") -> WarningMsg:
    return WarningMsg(severity, code, message, fix)


def cut_rect(x: float, y: float, w: float, h: float, *, kind: str = "cutout") -> CutPath:
    return CutPath(d=rect_path(x, y, w, h), kind=kind, bbox_hint=(x, y, x + w, y + h))


def cut_rounded_rect(x: float, y: float, w: float, h: float, r: float, *, kind: str = "cutout") -> CutPath:
    return CutPath(d=rounded_rect_path(x, y, w, h, r), kind=kind, bbox_hint=(x, y, x + w, y + h))


def cut_circle(cx: float, cy: float, r: float, *, kind: str = "cutout") -> CutPath:
    return CutPath(d=circle_path(cx, cy, r), kind=kind, bbox_hint=(cx - r, cy - r, cx + r, cy + r))


def cut_thumb_notch(width: float, y_top: float, radius: float, depth: float, *, kind: str = "notch") -> CutPath:
    cx = width / 2.0
    return CutPath(d=thumb_notch_path(width, y_top, radius, depth), kind=kind, bbox_hint=(cx - radius, y_top, cx + radius, y_top + depth))


def corner_relief_mm(*, thickness: float, kerf: float, clearance: float, outer_w: float, outer_d: float, wall_h: float) -> float:
    tab_depth, slot_depth = joint_depths_drawn(thickness=thickness, kerf_mm=kerf, clearance_mm=clearance)
    relief = max(float(thickness), tab_depth, slot_depth) + max(0.05, float(kerf) * 0.25)
    return relief


def corner_clearance_mm(
    *,
    thickness: float,
    kerf: float,
    clearance: float,
    target_finger_w: float,
    outer_w: float,
    outer_d: float,
    wall_h: float,
) -> float:
    """Reserved no-finger zone measured along each edge from a panel corner."""

    tab_depth, slot_depth = joint_depths_drawn(thickness=thickness, kerf_mm=kerf, clearance_mm=clearance)
    normal_depth = max(tab_depth, slot_depth)
    base = max(float(thickness), float(target_finger_w) / 2.0, 2.0 * float(kerf))
    relief = base + normal_depth
    return relief


def target_finger_width(thickness: float, finger_w: Optional[float]) -> float:
    return float(finger_w) if finger_w is not None else max(10.0, 3.0 * float(thickness))


def validate_common_dimensions(*, inner_w: float, inner_d: float, inner_h: float, thickness: float, kerf: float, clearance: float) -> List[WarningMsg]:
    warnings: List[WarningMsg] = []
    if thickness <= 0:
        warnings.append(warn("error", "THICKNESS_INVALID", "Material thickness must be greater than 0.", "Measure the material and enter a positive thickness."))
    if inner_w <= 0 or inner_d <= 0 or inner_h <= 0:
        warnings.append(warn("error", "INNER_DIMENSION_INVALID", "Internal dimensions must all be greater than 0.", "Increase width, depth, and height."))
    if kerf < 0:
        warnings.append(warn("error", "KERF_NEGATIVE", "Kerf must not be negative.", "Use 0 if kerf is unknown."))
    if kerf >= thickness and thickness > 0:
        warnings.append(warn("warn", "KERF_TOO_LARGE", "Kerf is greater than or equal to material thickness.", "Check units; kerf is usually around 0.1-0.3mm."))
    if clearance < -0.5:
        warnings.append(warn("warn", "CLEARANCE_TIGHT", "Clearance is very tight and may not assemble after cutting.", "Use a fit-test strip before final cutting."))
    if clearance > max(0.8, thickness * 0.35):
        warnings.append(warn("warn", "CLEARANCE_LOOSE", "Clearance is large and joints may wobble.", "Reduce clearance or use glue."))
    return warnings


def build_edge_pairs_for_box(
    *,
    thickness: float,
    finger_w: Optional[float],
    min_fingers: int,
    kerf: float,
    clearance: float,
    outer_w: float,
    outer_d: float,
    wall_h: float,
    front_panel_h: float,
    include_front: bool,
    prefix: str = "",
    finger_count_outer: Optional[int] = None,
    finger_count_vertical: Optional[int] = None,
) -> Dict[str, EdgePair]:
    pairs: Dict[str, EdgePair] = {}
    target = target_finger_width(thickness, finger_w)
    corner = corner_clearance_mm(
        thickness=thickness,
        kerf=kerf,
        clearance=clearance,
        target_finger_w=target,
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
    )

    def panel(name: str) -> str:
        return f"{prefix}{name}" if prefix else name

    def mk_pair(pid: str, family: str, a: EdgeKey, b: EdgeKey, length: float, start_with_tab_on_a: bool = True):
        explicit = finger_count_outer if family == EdgeFamily.OUTER else finger_count_vertical
        n = compute_finger_count(length, target, min_fingers=min_fingers, explicit=explicit)
        plan = build_finger_plan(length, count=n, kerf_mm=kerf, clearance_mm=clearance, start_with_tab_on_a=start_with_tab_on_a)
        pairs[pid] = EdgePair(id=pid, family=family, a=a, b=b, length=length, plan=plan)

    mk_pair(f"{prefix}bottom_back", EdgeFamily.OUTER, EdgeKey(panel("BOTTOM"), "top"), EdgeKey(panel("BACK"), "bottom"), outer_w - 2 * corner)
    mk_pair(f"{prefix}bottom_left", EdgeFamily.OUTER, EdgeKey(panel("BOTTOM"), "left"), EdgeKey(panel("LEFT"), "bottom"), outer_d - 2 * corner)
    mk_pair(f"{prefix}bottom_right", EdgeFamily.OUTER, EdgeKey(panel("BOTTOM"), "right"), EdgeKey(panel("RIGHT"), "bottom"), outer_d - 2 * corner)
    mk_pair(f"{prefix}corner_back_left", EdgeFamily.VERTICAL, EdgeKey(panel("BACK"), "left"), EdgeKey(panel("LEFT"), "right"), wall_h - 2 * corner)
    mk_pair(f"{prefix}corner_back_right", EdgeFamily.VERTICAL, EdgeKey(panel("BACK"), "right"), EdgeKey(panel("RIGHT"), "left"), wall_h - 2 * corner)
    if include_front:
        mk_pair(f"{prefix}bottom_front", EdgeFamily.OUTER, EdgeKey(panel("BOTTOM"), "bottom"), EdgeKey(panel("FRONT"), "bottom"), outer_w - 2 * corner)
        mk_pair(f"{prefix}corner_front_left", EdgeFamily.VERTICAL, EdgeKey(panel("FRONT"), "left"), EdgeKey(panel("LEFT"), "left"), front_panel_h - 2 * corner)
        mk_pair(f"{prefix}corner_front_right", EdgeFamily.VERTICAL, EdgeKey(panel("FRONT"), "right"), EdgeKey(panel("RIGHT"), "right"), front_panel_h - 2 * corner)
    return pairs


def build_open_box(
    *,
    preset: str,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    thickness: float,
    kerf: float,
    clearance: float,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    include_front: bool = True,
    front_h: Optional[float] = None,
    front_is_internal_height: bool = True,
    labels: bool = True,
    prefix: str = "",
    finger_count_outer: Optional[int] = None,
    finger_count_vertical: Optional[int] = None,
) -> BoxBuild:
    warnings = validate_common_dimensions(inner_w=inner_w, inner_d=inner_d, inner_h=inner_h, thickness=thickness, kerf=kerf, clearance=clearance)
    t = float(thickness)
    outer_w = float(inner_w) + 2 * t
    outer_d = float(inner_d) + 2 * t
    wall_h = float(inner_h) + t
    if front_h is None:
        front_panel_h = wall_h
    else:
        front_panel_h = float(front_h) + (t if front_is_internal_height else 0.0)
        front_panel_h = max(t * 1.5, min(front_panel_h, wall_h))

    def name(part: str) -> str:
        return f"{prefix}{part}" if prefix else part

    target = target_finger_width(thickness, finger_w)
    corner = corner_clearance_mm(
        thickness=t,
        kerf=kerf,
        clearance=clearance,
        target_finger_w=target,
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
    )
    graph = make_rectangular_box_graph(
        outer_w=outer_w,
        outer_d=outer_d,
        wall_h=wall_h,
        front_panel_h=front_panel_h,
        include_front=include_front,
        prefix=prefix,
        joint_margin=corner,
        finger_count_outer=finger_count_outer,
        finger_count_vertical=finger_count_vertical,
    )
    graph.compile(target_finger_w=target, min_fingers=min_fingers, kerf=kerf, clearance=clearance)
    specs = graph.panels
    edge_pairs = graph.edge_pairs
    meta_corner_relief = corner

    if labels:
        for spec in specs.values():
            spec.labels = [(spec.name, (spec.width / 2, spec.height / 2))]

    render_params = JointRenderParams(thickness=t, kerf_mm=kerf, clearance_mm=clearance)
    order = [name("BOTTOM"), name("BACK"), name("LEFT"), name("RIGHT")]
    if include_front:
        order.append(name("FRONT"))
    panels = [render_panel_from_spec(specs[n], joint_params=render_params, edge_pairs=edge_pairs) for n in order]

    for pair in edge_pairs.values():
        pitch = pair.length / max(1, pair.plan.count)
        if pitch < max(4.0, t * 1.4):
            warnings.append(warn("warn", "TABS_SMALL", f"Edge {pair.id} has small {pitch:.1f}mm tabs.", "Increase finger width or panel size."))

    meta: Dict[str, object] = {
        "template_id": preset,
        "dimensions": {
            "inner": {"w": inner_w, "d": inner_d, "h": inner_h},
            "outer": {"w": outer_w, "d": outer_d, "h": wall_h},
            "front_panel_h": front_panel_h,
            "corner_relief": meta_corner_relief,
        },
        "fabrication": {
            "thickness": thickness,
            "kerf": kerf,
            "fit_clearance": clearance,
            "target_finger_w": target,
            "kerf_convention": "kerf is full cut width; burn radius is kerf/2",
            "joint_rule": "open-edge slot_depth_drawn = thickness + clearance - kerf; tab_depth_drawn = thickness + kerf",
            "width_rule": "tab/slot segment widths are kerf/clearance compensated then normalized per edge",
        },
        "edge_pairs": [pair.to_meta(thickness=thickness, kerf_mm=kerf, clearance_mm=clearance) for pair in edge_pairs.values()],
        "assembly_graph": {
            "model": "rectangular_box_v1",
            "panels": graph.panel_edge_meta(),
            "joint_pairs": [pair.to_meta(thickness=thickness, kerf_mm=kerf, clearance_mm=clearance) for pair in edge_pairs.values()],
        },
    }
    return BoxBuild(panels=panels, warnings=warnings, meta=meta, edge_pairs=edge_pairs, specs=specs, outer_w=outer_w, outer_d=outer_d, wall_h=wall_h, front_panel_h=front_panel_h)


def panel_from_rect(name: str, w: float, h: float, *, labels: bool = True, cutouts: Optional[List[CutPath]] = None, notes: Optional[List[str]] = None) -> Panel:
    panel = Panel(name=name, outline=[(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)], cutouts=cutouts or [], notes=notes or [])
    if labels:
        panel.labels.append((name, (w / 2, h / 2)))
    return panel
