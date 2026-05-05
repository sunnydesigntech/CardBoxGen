#!/usr/bin/env python3
"""Regenerate checked example SVGs from the package API."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

# Allow running this script directly (sys.path[0] is examples/).
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cardboxgen.api import generate_svg
from cardboxgen.validation import validate_template_params


def write_svg(out_dir: Path, filename: str, template_id: str, params: dict) -> None:
    result = generate_svg(template_id, params)
    (out_dir / filename).write_text(result["svg"], encoding="utf-8")


def write_invalid_report(out_dir: Path) -> None:
    validation = validate_template_params(
        "tray_open_front",
        {
            "inner_w": 12,
            "inner_d": 12,
            "inner_h": 8,
            "thickness": 3,
            "kerf": 0.2,
            "fit_clearance": 0.15,
        },
    )
    (out_dir / "invalid_dimension_report.json").write_text(json.dumps(validation.to_dict(), indent=2), encoding="utf-8")


def generate(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    common = {
        "inner_w": 135,
        "inner_d": 90,
        "inner_h": 225,
        "thickness": 3,
        "kerf": 0.2,
        "fit_clearance": 0.15,
        "labels": True,
        "max_row_width": 340,
    }
    write_svg(out, "tray_open_front.svg", "tray_open_front", {**common, "scoop": True})
    write_svg(out, "dispenser_slot_front.svg", "dispenser_slot_front", {**common, "slot_width": 86, "slot_height": 18, "slot_y_from_bottom": 38})
    write_svg(out, "window_front.svg", "window_front", {**common, "window_margin": 14})
    write_svg(out, "box_with_lid.svg", "box_with_lid", {**common, "lid": True, "lid_height": 30, "lid_clearance": 0.4})
    write_svg(out, "divider_rack.svg", "divider_rack", {**common, "divider_count": 4})
    write_svg(
        out,
        "card_shoe.svg",
        "card_shoe",
        {"card_w": 63, "card_h": 88, "card_t": 0.35, "capacity": 60, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15, "labels": True, "max_row_width": 340},
    )
    write_svg(
        out,
        "candy_machine_rotary_layered.svg",
        "candy_machine_rotary_layered",
        {
            "max_piece": 18,
            "irregular": False,
            "hopper_h": 90,
            "depth_layers_total": 8,
            "wheel_layers": 3,
            "screw_d": 3.2,
            "screw_margin": 10,
            "axle_d": 6,
            "thickness": 3,
            "kerf": 0.2,
            "fit_clearance": 0.15,
            "labels": True,
            "max_row_width": 340,
        },
    )
    write_svg(
        out,
        "calibration_mating_strips.svg",
        "calibration",
        {"thickness": 3.0, "kerf": 0.2, "clearance_values": [-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20], "labels": True},
    )
    write_invalid_report(out)


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(__file__)))
