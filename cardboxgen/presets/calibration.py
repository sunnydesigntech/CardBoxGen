"""Calibration and fit-test presets."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ..joints import joint_depths_drawn
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
    strip_w = 38.0
    strip_h = 16.0
    slot_len = 24.0
    for c in values:
        _, slot_w = joint_depths_drawn(thickness=thickness, kerf_mm=kerf, clearance_mm=float(c))
        name = f"FIT_{c:+.2f}mm".replace("+", "plus_").replace("-", "minus_").replace(".", "p")
        panel = panel_from_rect(name, strip_w, strip_h, labels=False, cutouts=[cut_rect((strip_w - slot_w) / 2, (strip_h - slot_len) / 2, slot_w, slot_len, kind="fit_slot")])
        if labels:
            panel.labels.append((f"t={thickness:g} k={kerf:g} c={c:+.2f}", (2.0, strip_h - 2.0)))
        panels.append(panel)
    meta = {
        "template_id": "calibration",
        "fabrication": {"thickness": thickness, "kerf": kerf},
        "clearance_values": values,
        "description": "Fit-test strips with drawn slot width/depth thickness + clearance - kerf.",
    }
    return panels, warnings, meta
