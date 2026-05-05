"""Layered rotary candy dispenser preset."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ..geometry import circle_outline
from ..models import WarningMsg
from ..panels import CutPath, Panel
from .common import cut_circle, cut_rounded_rect, panel_from_rect, warn


def build_candy_machine_rotary_layered(
    *,
    max_piece: float,
    irregular: bool,
    hopper_h: float,
    depth_layers_total: int,
    wheel_layers: int,
    screw_d: float,
    screw_margin: float,
    axle_d: float,
    add_feet: bool = False,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
    labels: bool = True,
    **kwargs,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    t = float(thickness)
    p = float(max_piece)
    hopper_h = float(hopper_h)
    screw_d = float(screw_d)
    screw_margin = float(screw_margin)
    axle_d = float(axle_d)
    depth_layers_total = int(depth_layers_total)
    wheel_layers = int(wheel_layers)

    warnings: List[WarningMsg] = []
    if t <= 0:
        warnings.append(warn("error", "THICKNESS_INVALID", "Material thickness must be greater than 0.", "Measure the material and enter a positive thickness."))
    if p <= 0:
        warnings.append(warn("error", "CM_MAX_PIECE_INVALID", "max_piece must be > 0.", "Increase max_piece."))
        p = max(1.0, p)
    if irregular:
        warnings.append(warn("warn", "CM_IRREGULAR_FLOW", "Irregular pieces bridge more easily in rotary dispensers.", "Prototype at low scale and increase chute clearances."))
    if hopper_h < 40.0:
        warnings.append(warn("warn", "CM_HOPPER_LOW", "Hopper height is small; capacity may be low.", "Increase hopper_h."))
    if depth_layers_total < 2:
        warnings.append(warn("error", "CM_LAYERS_TOO_FEW", "depth_layers_total must be at least 2.", "Use 8 for a typical 3mm stacked mechanism."))
        depth_layers_total = 2
    if wheel_layers < 1:
        warnings.append(warn("error", "CM_WHEEL_LAYERS_TOO_FEW", "wheel_layers must be at least 1.", "Use 2-4 wheel spacer layers."))
        wheel_layers = 1
    if wheel_layers >= depth_layers_total:
        warnings.append(warn("error", "CM_LAYER_SPLIT_INVALID", "wheel_layers must be less than depth_layers_total.", "Increase depth_layers_total or reduce wheel_layers."))
        wheel_layers = max(1, depth_layers_total - 1)

    hopper_layers = max(1, depth_layers_total - wheel_layers)
    safety = 2.5 if irregular else 1.5
    pocket_d = p + safety
    pocket_r = pocket_d / 2.0
    pocket_count = max(8, int(round(2 * math.pi * (pocket_d * 1.7) / max(10.0, pocket_d))))
    if pocket_count % 2:
        pocket_count += 1
    wheel_r = max(28.0, (pocket_count * pocket_d / (2 * math.pi)) * 1.30)
    wheel_d = 2 * wheel_r
    feed_w = max(pocket_d * 0.9, p * 1.25)
    feed_h = max(10.0, pocket_d * 0.9)
    chute_w = pocket_d + (3.0 if irregular else 2.0)
    chute_h = max(12.0, pocket_d * 1.1)

    if chute_w <= p * 1.10:
        warnings.append(warn("error", "CM_CHUTE_TOO_NARROW", "Chute width is too close to max piece size.", "Increase max_piece safety by enabling irregular or scale the mechanism up."))
    wall_between = (2 * math.pi * wheel_r / pocket_count) - pocket_d
    if wall_between < max(2.0, t * 0.7):
        warnings.append(warn("error", "CM_POCKET_WALL_TOO_THIN", f"Wall between pockets is about {wall_between:.1f}mm.", "Increase wheel diameter or reduce max_piece."))

    side_wall = max(10.0, screw_margin + screw_d)
    wheel_clear = max(2.0, fit_clearance + 0.6)
    wheel_cavity_r = wheel_r + wheel_clear
    chute_bottom_margin = max(14.0, screw_margin + screw_d + 4.0)
    wheel_top_y = side_wall + max(12.0, hopper_h * 0.20)
    cy = wheel_top_y + wheel_cavity_r
    plate_w = max(wheel_cavity_r * 2 + side_wall * 2, 140.0)
    plate_h = max(cy + wheel_cavity_r + chute_bottom_margin, wheel_d + hopper_h + side_wall * 2)
    cx = plate_w / 2.0

    if max(plate_w, plate_h) > 450:
        warnings.append(warn("warn", "CM_PLATE_LARGE", "Some plates are large for small desktop laser beds.", "Reduce max_piece or hopper_h, or use a larger sheet."))

    hopper_x = side_wall
    hopper_y = side_wall
    hopper_w = plate_w - 2 * side_wall
    hopper_cut_h = max(40.0, min(hopper_h, plate_h - side_wall * 2 - wheel_cavity_r * 0.6))
    feed_x = cx - feed_w / 2
    feed_y = hopper_y + hopper_cut_h - feed_h * 0.6
    exit_w = max(chute_w, pocket_d * 0.9)
    exit_h = max(10.0, pocket_d * 0.8)
    exit_x = cx - exit_w / 2
    exit_y = cy + wheel_cavity_r - exit_h * 0.4
    chute_x = cx - chute_w / 2
    chute_y = min(exit_y + exit_h * 0.7, plate_h - chute_bottom_margin - chute_h)
    opening_w = max(chute_w + 6.0, 24.0)
    opening_h = max(14.0, chute_h * 0.8)
    opening_x = cx - opening_w / 2
    opening_y = plate_h - chute_bottom_margin - opening_h

    hole_r = max(0.6, screw_d / 2.0)
    screw_pts = [
        (screw_margin, screw_margin),
        (plate_w - screw_margin, screw_margin),
        (screw_margin, plate_h - screw_margin),
        (plate_w - screw_margin, plate_h - screw_margin),
    ]
    if screw_margin < max(6.0, screw_d * 2):
        warnings.append(warn("warn", "CM_SCREW_MARGIN_SMALL", "Screw holes are close to the plate edge.", "Increase screw_margin to 10-12mm."))

    plate_outline = [(0.0, 0.0), (plate_w, 0.0), (plate_w, plate_h), (0.0, plate_h)]

    def screw_holes() -> List[CutPath]:
        return [cut_circle(x, y, hole_r, kind="screw_hole") for x, y in screw_pts]

    panels: List[Panel] = []
    front = Panel(
        "FRONT_ACRYLIC",
        plate_outline,
        screw_holes() + [cut_circle(cx, cy, axle_d / 2.0, kind="axle_hole"), cut_rounded_rect(opening_x, opening_y, opening_w, opening_h, 3.0, kind="dispense_opening")],
    )
    back = Panel("BACK_PLATE", plate_outline, screw_holes() + [cut_circle(cx, cy, axle_d / 2.0, kind="axle_hole")])
    if labels:
        front.labels.append(("FRONT_ACRYLIC", (plate_w * 0.22, plate_h * 0.55)))
        back.labels.append(("BACK_PLATE", (plate_w * 0.30, plate_h * 0.55)))
    panels.extend([front, back])

    hopper_cutouts = screw_holes() + [
        cut_circle(cx, cy, axle_d / 2.0 + 0.6, kind="axle_clearance"),
        cut_rounded_rect(hopper_x, hopper_y, hopper_w, hopper_cut_h, 6.0, kind="hopper_cavity"),
    ]
    for i in range(hopper_layers):
        panel = Panel(f"HOPPER_SPACER_{i + 1}", plate_outline, list(hopper_cutouts))
        if labels:
            panel.labels.append((panel.name, (plate_w * 0.22, plate_h * 0.58)))
        panels.append(panel)

    wheel_cutouts = screw_holes() + [
        cut_circle(cx, cy, axle_d / 2.0 + 0.8, kind="axle_clearance"),
        cut_circle(cx, cy, wheel_cavity_r, kind="wheel_cavity"),
        cut_rounded_rect(feed_x, feed_y, feed_w, feed_h, 3.0, kind="feed_window"),
        cut_rounded_rect(exit_x, exit_y, exit_w, exit_h, 3.0, kind="exit_window"),
        cut_rounded_rect(chute_x, chute_y, chute_w, chute_h, 3.0, kind="chute"),
    ]
    for i in range(wheel_layers):
        panel = Panel(f"WHEEL_SPACER_{i + 1}", plate_outline, list(wheel_cutouts))
        if labels:
            panel.labels.append((panel.name, (plate_w * 0.22, plate_h * 0.62)))
        panels.append(panel)

    wheel_outline = circle_outline(wheel_r)
    pocket_ring_r = wheel_r - pocket_d * 0.85
    wheel_part_cutouts = [cut_circle(wheel_r, wheel_r, axle_d / 2.0, kind="axle_hole")]
    for i in range(pocket_count):
        ang = 2 * math.pi * i / pocket_count
        px = wheel_r + pocket_ring_r * math.cos(ang)
        py = wheel_r + pocket_ring_r * math.sin(ang)
        wheel_part_cutouts.append(cut_circle(px, py, pocket_r, kind="metering_pocket"))
    wheel = Panel("WHEEL", wheel_outline, wheel_part_cutouts)
    if labels:
        wheel.labels.append(("WHEEL", (wheel_r * 0.45, wheel_r * 1.05)))
    panels.append(wheel)

    knob_r = max(14.0, axle_d * 2.2)
    knob = Panel("KNOB", circle_outline(knob_r), [cut_circle(knob_r, knob_r, axle_d / 2.0, kind="axle_hole")])
    if labels:
        knob.labels.append(("KNOB", (knob_r * 0.55, knob_r * 1.05)))
    panels.append(knob)

    if add_feet:
        panels.append(panel_from_rect("FOOT_1", max(30.0, plate_w * 0.28), 12.0, labels=labels))
        panels.append(panel_from_rect("FOOT_2", max(30.0, plate_w * 0.28), 12.0, labels=labels))

    meta = {
        "template_id": "candy_machine_rotary_layered",
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance},
        "mechanical_assumptions": [
            "Educational/prototype mechanism only; not food-safe machinery.",
            "Dry flowing solids only.",
            "Irregular shapes can bridge in the hopper or chute.",
            "Cut and test a prototype before relying on the dispenser.",
        ],
        "inputs": {
            "max_piece": max_piece,
            "irregular": irregular,
            "hopper_h": hopper_h,
            "depth_layers_total": depth_layers_total,
            "wheel_layers": wheel_layers,
            "screw_d": screw_d,
            "screw_margin": screw_margin,
            "axle_d": axle_d,
            "add_feet": add_feet,
        },
        "derived": {
            "pocket_d": pocket_d,
            "pocket_count": pocket_count,
            "wheel_d": wheel_d,
            "chute_w": chute_w,
            "plate_w": plate_w,
            "plate_h": plate_h,
            "hopper_layers": hopper_layers,
        },
        "warnings": [w.to_dict() for w in warnings],
    }
    return panels, warnings, meta
