"""Slot-front dispenser preset."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..models import WarningMsg
from ..panels import Panel
from .common import build_open_box, cut_rect, cut_thumb_notch, warn


def build_dispenser_slot_front(
    *,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    slot_width: float = 80.0,
    slot_height: float = 18.0,
    slot_y_from_bottom: float = 35.0,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    labels: bool = True,
    thumb_notch_radius: float = 10.0,
    thumb_notch_depth: float = 8.0,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    box = build_open_box(
        preset="dispenser_slot_front",
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
    margin = max(thickness * 2.0, 6.0)
    sw = float(slot_width)
    sh = float(slot_height)
    sx = (box.outer_w - sw) / 2.0
    sy = box.front_panel_h - float(slot_y_from_bottom) - sh
    if sw <= 0 or sh <= 0:
        warnings.append(warn("error", "SLOT_INVALID", "Slot width and height must be positive.", "Increase slot_width and slot_height."))
        sw = max(1.0, sw)
        sh = max(1.0, sh)
    if sx < margin or sx + sw > box.outer_w - margin:
        warnings.append(warn("error", "SLOT_TOO_WIDE", "Dispensing slot collides with side joints or edge margin.", "Reduce slot_width or increase inner_w."))
        sw = max(1.0, min(sw, box.outer_w - 2 * margin))
        sx = (box.outer_w - sw) / 2.0
    if sy < margin or sy + sh > box.front_panel_h - margin:
        warnings.append(warn("error", "SLOT_VERTICAL_COLLISION", "Dispensing slot collides with top/bottom material margin.", "Move slot_y_from_bottom or reduce slot_height."))
        sy = min(max(sy, margin), max(margin, box.front_panel_h - margin - sh))
    for panel in box.panels:
        if panel.name == "FRONT":
            panel.cutouts.append(cut_rect(sx, sy, sw, sh))
            panel.cutouts.append(cut_thumb_notch(box.outer_w, 0.0, min(thumb_notch_radius, box.outer_w / 4), min(thumb_notch_depth, box.front_panel_h / 4)))
            break
    box.meta["features"] = {"slot": {"x": sx, "y": sy, "w": sw, "h": sh}, "thumb_notch": True}
    box.meta["warnings"] = [w.to_dict() for w in warnings]
    return box.panels, warnings, box.meta
