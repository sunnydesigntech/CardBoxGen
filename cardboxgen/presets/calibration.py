"""Calibration and fit-test presets."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ..fabrication import drawn_slot_depth_for_target, drawn_slot_width_for_target
from ..models import WarningMsg
from ..panels import Panel
from .common import cut_rect, panel_from_rect


def build_calibration(
    *,
    thickness: float,
    kerf: float = 0.2,
    clearance_values: Optional[Iterable[float]] = None,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    values = list(clearance_values if clearance_values is not None else [-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20, 0.30])
    panels: List[Panel] = []
    warnings: List[WarningMsg] = []
    reference = panel_from_rect("REFERENCE_50x20MM", 50.0, 20.0, labels=False)
    if labels:
        reference.labels.append(("REFERENCE 50 x 20 mm", (2.0, 12.0)))
    panels.append(reference)
    strip_w = 38.0
    strip_h = 16.0
    slot_len = 24.0
    for c in values:
        target = float(thickness) + float(c)
        slot_w = max(0.2, drawn_slot_width_for_target(target, kerf))
        slot_depth = max(0.2, drawn_slot_depth_for_target(target, kerf))
        name = f"FIT_{c:+.2f}mm".replace("+", "plus_").replace("-", "minus_").replace(".", "p")
        panel = panel_from_rect(
            name,
            strip_w,
            strip_h,
            labels=False,
            cutouts=[
                cut_rect((strip_w - slot_w) / 2, (strip_h - slot_len) / 2, slot_w, slot_len, kind="width_fit_slot"),
                cut_rect(4.0, strip_h - slot_depth, 6.0, slot_depth, kind="depth_fit_notch"),
            ],
        )
        if labels:
            panel.labels.append((f"t={thickness:g} k={kerf:g} c={c:+.2f}", (2.0, strip_h - 2.0)))
        panels.append(panel)
    meta = {
        "template_id": "calibration",
        "fabrication": {"thickness": thickness, "kerf": kerf},
        "clearance_values": values,
        "description": "Fit-test strips include width-fit slots, depth-fit notches, and a 50 x 20 mm scale reference.",
    }
    return panels, warnings, meta
