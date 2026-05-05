"""Window-front storage box/tray preset."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..models import WarningMsg
from ..panels import Panel
from .common import build_open_box, cut_rounded_rect, cut_thumb_notch, warn


def build_window_front(
    *,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    window_margin: float = 12.0,
    window_corner_r: float = 6.0,
    thumb_notch_radius: float = 10.0,
    thumb_notch_depth: float = 8.0,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    box = build_open_box(
        preset="window_front",
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
    margin = max(float(window_margin), thickness * 2.0)
    ww = box.outer_w - 2 * margin
    wh = box.front_panel_h - 2 * margin
    if ww < 10 or wh < 10:
        warnings.append(warn("error", "WINDOW_TOO_LARGE", "Window margin leaves too little material around the cutout.", "Increase panel size or reduce window_margin."))
        ww = max(1.0, ww)
        wh = max(1.0, wh)
    if margin < thickness * 2:
        warnings.append(warn("warn", "WINDOW_MARGIN_SMALL", "Window margin is close to the joint area.", "Use at least two material thicknesses as margin."))
    for panel in box.panels:
        if panel.name == "FRONT":
            panel.cutouts.append(cut_rounded_rect(margin, margin, ww, wh, window_corner_r))
            panel.cutouts.append(cut_thumb_notch(box.outer_w, 0.0, min(thumb_notch_radius, box.outer_w / 4), min(thumb_notch_depth, box.front_panel_h / 4)))
            break
    box.meta["features"] = {"window": {"x": margin, "y": margin, "w": ww, "h": wh, "r": window_corner_r}, "thumb_notch": True}
    box.meta["warnings"] = [w.to_dict() for w in warnings]
    return box.panels, warnings, box.meta
