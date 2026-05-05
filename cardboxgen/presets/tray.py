"""Open-front tray preset."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..models import WarningMsg
from ..panels import Panel
from .common import build_open_box, cut_thumb_notch, warn


def build_tray_open_front(
    *,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    front_h: Optional[float] = None,
    scoop: bool = True,
    scoop_r: float = 22.0,
    scoop_depth: float = 16.0,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    min_fingers: int = 3,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    fh = float(front_h) if front_h is not None else max(thickness * 2.0, min(inner_h * 0.45, 32.0))
    box = build_open_box(
        preset="tray_open_front",
        inner_w=inner_w,
        inner_d=inner_d,
        inner_h=inner_h,
        thickness=thickness,
        kerf=kerf,
        clearance=fit_clearance,
        finger_w=finger_w,
        min_fingers=min_fingers,
        include_front=True,
        front_h=fh,
        labels=labels,
        finger_count_outer=kwargs.get("finger_count_outer"),
        finger_count_vertical=kwargs.get("finger_count_vertical"),
    )
    warnings = list(box.warnings)
    if fh >= inner_h * 0.8:
        warnings.append(warn("warn", "TRAY_FRONT_TALL", "Front height is high for an open-front tray.", "Reduce front_h for easier access."))
    if scoop:
        radius = min(float(scoop_r), box.outer_w / 2 - thickness)
        depth = min(float(scoop_depth), max(thickness, box.front_panel_h - thickness))
        if radius <= thickness or depth <= thickness:
            warnings.append(warn("warn", "SCOOP_SMALL", "Scoop notch is too small to be useful.", "Increase scoop radius or depth."))
        for panel in box.panels:
            if panel.name == "FRONT":
                panel.cutouts.append(cut_thumb_notch(box.outer_w, 0.0, radius, depth))
                break
    box.meta["features"] = {"front_inner_h": fh, "scoop": scoop, "scoop_r": scoop_r, "scoop_depth": scoop_depth}
    box.meta["warnings"] = [w.to_dict() for w in warnings]
    return box.panels, warnings, box.meta
