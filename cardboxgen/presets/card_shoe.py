"""Front-draw card shoe dispenser."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ..models import WarningMsg
from ..panels import CutPath, Panel
from .common import build_open_box, cut_rect, cut_rounded_rect, panel_from_rect, warn


def build_card_shoe(
    *,
    card_w: float,
    card_h: float,
    card_t: float,
    capacity: int,
    ramp_angle_deg: float = 12.0,
    draw_slot_height: Optional[float] = None,
    follower: bool = False,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    side_clear = float(kwargs.get("side_clearance", 1.0))
    back_clear = float(kwargs.get("back_clearance", 2.0))
    top_clear = float(kwargs.get("top_clearance", 8.0))
    capacity = int(capacity)
    stack_h = max(0.0, capacity * float(card_t))
    inner_w = float(card_w) + 2 * side_clear
    inner_d = float(card_h) + back_clear + 2.0
    inner_h = stack_h + top_clear + max(6.0, thickness * 2)

    box = build_open_box(
        preset="card_shoe",
        inner_w=inner_w,
        inner_d=inner_d,
        inner_h=inner_h,
        thickness=thickness,
        kerf=kerf,
        clearance=fit_clearance,
        finger_w=finger_w,
        min_fingers=min_fingers,
        include_front=True,
        labels=labels,
        finger_count_outer=kwargs.get("finger_count_outer"),
        finger_count_vertical=kwargs.get("finger_count_vertical"),
    )
    warnings = list(box.warnings)
    if card_t <= 0:
        warnings.append(warn("error", "CARD_THICKNESS_INVALID", "Card thickness must be greater than 0.", "Measure one card or a stack and divide by count."))
    if capacity <= 0:
        warnings.append(warn("error", "CAPACITY_INVALID", "Capacity must be greater than 0.", "Increase capacity."))
    if ramp_angle_deg < 6:
        warnings.append(warn("warn", "RAMP_ANGLE_LOW", "Ramp angle is shallow and cards may not slide reliably.", "Use 8-15 degrees or add a follower."))
    if ramp_angle_deg > 18:
        warnings.append(warn("warn", "RAMP_ANGLE_HIGH", "Ramp angle is steep and stack pressure/friction may increase.", "Use 8-15 degrees for most card stock."))
    if stack_h > 70:
        warnings.append(warn("warn", "CARD_STACK_TALL", "Tall card stacks can bind under their own weight.", "Reduce capacity or add a follower."))

    slot_h = float(draw_slot_height) if draw_slot_height is not None else max(1.0, min(3.0, card_t + 0.6))
    slot_w = min(box.outer_w - 2 * thickness * 2, card_w * 0.9)
    lip_h = max(8.0, thickness * 3)
    if slot_h < card_t + 0.25:
        warnings.append(warn("error", "DRAW_SLOT_TOO_SHORT", "Draw slot is too short for one card.", "Increase draw_slot_height."))
    if slot_h > card_t + 2.5:
        warnings.append(warn("warn", "DRAW_SLOT_TOO_TALL", "Draw slot may release multiple cards.", "Reduce draw_slot_height or add a hold-down lip."))

    for panel in box.panels:
        if panel.name == "FRONT":
            sx = (box.outer_w - slot_w) / 2.0
            panel.cutouts.append(cut_rect(sx, box.front_panel_h - lip_h, slot_w, slot_h, kind="draw_slot"))
            panel.cutouts.append(cut_rounded_rect(max(thickness * 2, sx - 4.0), max(thickness * 3, 12.0), min(box.outer_w - 4 * thickness, slot_w + 8.0), min(70.0, box.front_panel_h * 0.45), 6.0, kind="view_window"))
            break

    ramp_w = inner_w
    ramp_d = inner_d
    ramp = panel_from_rect("RAMP_PLATE", ramp_w, ramp_d, labels=labels, notes=["Mount at the requested ramp angle using the ramp blocks."])
    rise = max(6.0, min(inner_h * 0.65, ramp_d * math.tan(math.radians(float(ramp_angle_deg)))))
    block = panel_from_rect("RAMP_BACK_BLOCK", max(16.0, thickness * 6), rise, labels=labels)
    lip = panel_from_rect("HOLD_DOWN_LIP", inner_w, max(8.0, thickness * 3), labels=labels)
    extra = [ramp, block, lip]
    if follower:
        extra.append(panel_from_rect("FOLLOWER", inner_w, max(20.0, card_h * 0.6), labels=labels))

    panels = list(box.panels) + extra
    box.meta["features"] = {
        "derived_inner": {"w": inner_w, "d": inner_d, "h": inner_h},
        "card": {"w": card_w, "h": card_h, "t": card_t, "capacity": capacity, "stack_h": stack_h},
        "draw_slot": {"w": slot_w, "h": slot_h},
        "ramp": {"angle_deg": ramp_angle_deg, "rise": rise},
        "follower": follower,
    }
    box.meta["warnings"] = [w.to_dict() for w in warnings]
    return panels, warnings, box.meta
