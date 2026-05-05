"""Divider rack preset with slotted internal dividers."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..joints import joint_depths_drawn
from ..models import WarningMsg
from ..panels import Panel
from .common import build_open_box, cut_rect, panel_from_rect, warn


def _divider_panel(name: str, width: float, height: float, tab_w: float, tab_depth: float, *, labels: bool) -> Panel:
    cx = width / 2.0
    tab_w = min(max(tab_w, 2.0), width * 0.8)
    outline = [
        (0.0, 0.0),
        (width, 0.0),
        (width, height),
        (cx + tab_w / 2, height),
        (cx + tab_w / 2, height + tab_depth),
        (cx - tab_w / 2, height + tab_depth),
        (cx - tab_w / 2, height),
        (0.0, height),
    ]
    panel = Panel(name=name, outline=outline, notes=["Divider tab fits a matching slot in BOTTOM."])
    if labels:
        panel.labels.append((name, (width / 2, height / 2)))
    return panel


def build_divider_rack(
    *,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    divider_count: int = 3,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    bays = int(divider_count)
    box = build_open_box(
        preset="divider_rack",
        inner_w=inner_w,
        inner_d=inner_d,
        inner_h=inner_h,
        thickness=thickness,
        kerf=kerf,
        clearance=fit_clearance,
        finger_w=finger_w,
        min_fingers=min_fingers,
        include_front=True,
        front_h=max(thickness * 2.0, min(inner_h * 0.45, 30.0)),
        labels=labels,
        finger_count_outer=kwargs.get("finger_count_outer"),
        finger_count_vertical=kwargs.get("finger_count_vertical"),
    )
    warnings = list(box.warnings)
    if bays < 2:
        warnings.append(warn("error", "DIVIDER_COUNT_TOO_LOW", "divider_count must be at least 2 bays.", "Increase divider_count."))
        bays = 2
    if bays > 12:
        warnings.append(warn("warn", "DIVIDER_COUNT_HIGH", "Many bays create narrow compartments and fragile slots.", "Reduce divider_count or increase width."))

    _, slot_w = joint_depths_drawn(thickness=thickness, kerf_mm=kerf, clearance_mm=fit_clearance)
    slot_len = max(10.0, inner_d - 12.0)
    slot_y = thickness + max(6.0, thickness * 2.0)
    usable_w = inner_w
    spacing = usable_w / bays
    if spacing < thickness * 3:
        warnings.append(warn("error", "DIVIDER_BAYS_TOO_NARROW", "Divider bays are too narrow for the material thickness.", "Reduce divider_count or increase inner_w."))

    bottom = next((p for p in box.panels if p.name == "BOTTOM"), None)
    dividers: List[Panel] = []
    for i in range(1, bays):
        x = thickness + i * spacing - slot_w / 2.0
        if bottom is not None:
            bottom.cutouts.append(cut_rect(x, slot_y, slot_w, slot_len, kind="divider_slot"))
        dividers.append(_divider_panel(f"DIVIDER_{i}", max(10.0, inner_d), max(10.0, inner_h), tab_w=max(8.0, thickness * 3), tab_depth=max(4.0, thickness * 1.5), labels=labels))

    panels = list(box.panels) + dividers
    box.meta["features"] = {
        "divider_bays": bays,
        "divider_count": max(0, bays - 1),
        "slot_width_drawn": slot_w,
        "slot_length": slot_len,
        "assembly_note": "Dividers include lower tabs and BOTTOM includes matching slot cutouts.",
    }
    box.meta["warnings"] = [w.to_dict() for w in warnings]
    return panels, warnings, box.meta
