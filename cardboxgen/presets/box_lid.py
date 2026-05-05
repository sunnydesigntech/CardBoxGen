"""Base box with a separate slip lid."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..models import WarningMsg
from ..panels import Panel
from .common import build_open_box, cut_thumb_notch, warn


def _rename_lid_panel(panel: Panel) -> Panel:
    mapping = {
        "LID_BOTTOM": "LID_TOP",
        "LID_BACK": "LID_BACK",
        "LID_LEFT": "LID_LEFT",
        "LID_RIGHT": "LID_RIGHT",
        "LID_FRONT": "LID_FRONT",
    }
    panel.name = mapping.get(panel.name, panel.name)
    panel.labels = [(panel.name, pos) for _, pos in panel.labels]
    return panel


def build_box_with_lid(
    *,
    inner_w: float,
    inner_d: float,
    inner_h: float,
    lid: bool = True,
    lid_height: float = 25.0,
    lid_clearance: float = 0.4,
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
    base = build_open_box(
        preset="box_with_lid",
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
    warnings = list(base.warnings)
    panels = list(base.panels)
    edge_meta = list(base.meta.get("edge_pairs", []))

    if lid:
        if lid_clearance < 0:
            warnings.append(warn("warn", "LID_CLEARANCE_NEGATIVE", "Lid clearance is negative and may not fit.", "Use a positive lid_clearance."))
        # The lid must slide over the outside of the base, so its internal cavity
        # is the base outside plus the requested slip clearance.
        lid_inner_w = inner_w + 2 * thickness + 2 * lid_clearance
        lid_inner_d = inner_d + 2 * thickness + 2 * lid_clearance
        lid_inner_h = max(thickness * 2.0, float(lid_height))
        lid_box = build_open_box(
            preset="box_with_lid_lid",
            inner_w=lid_inner_w,
            inner_d=lid_inner_d,
            inner_h=lid_inner_h,
            thickness=thickness,
            kerf=kerf,
            clearance=fit_clearance,
            finger_w=finger_w,
            min_fingers=min_fingers,
            include_front=True,
            labels=labels,
            prefix="LID_",
            finger_count_outer=kwargs.get("finger_count_outer"),
            finger_count_vertical=kwargs.get("finger_count_vertical"),
        )
        warnings.extend(lid_box.warnings)
        for panel in lid_box.panels:
            if panel.name == "LID_FRONT":
                panel.cutouts.append(cut_thumb_notch(lid_box.outer_w, 0.0, min(thumb_notch_radius, lid_box.outer_w / 4), min(thumb_notch_depth, lid_box.front_panel_h / 4)))
            panels.append(_rename_lid_panel(panel))
        for pair in lid_box.meta.get("edge_pairs", []):
            pair = dict(pair)
            for side in ("a", "b"):
                endpoint = dict(pair[side])
                if endpoint.get("panel") == "LID_BOTTOM":
                    endpoint["panel"] = "LID_TOP"
                pair[side] = endpoint
            edge_meta.append(pair)
        base.meta["lid"] = {
            "enabled": True,
            "inner": {"w": lid_inner_w, "d": lid_inner_d, "h": lid_inner_h},
            "clearance": lid_clearance,
        }
    else:
        warnings.append(warn("info", "LID_DISABLED", "Lid parts were not generated.", "Enable lid if a slip lid is needed."))
        base.meta["lid"] = {"enabled": False}

    base.meta["edge_pairs"] = edge_meta
    base.meta["warnings"] = [w.to_dict() for w in warnings]
    return panels, warnings, base.meta
