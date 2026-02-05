#!/usr/bin/env python3

import os
import sys

# Allow running this script directly (sys.path[0] is examples/).
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import cardboxgen_v0_1 as gen


def generate(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    examples = [
        (
            "tray_open_front.svg",
            gen.BoxParams(
                preset="tray_open_front",
                inner_width=135,
                inner_depth=90,
                inner_height=225,
                thickness=3,
                kerf_mm=0.2,
                clearance_mm=0.15,
                scoop=True,
                lid=False,
                labels=True,
                sheet_width=340,
            ),
        ),
        (
            "dispenser_slot_front.svg",
            gen.BoxParams(
                preset="dispenser_slot_front",
                inner_width=135,
                inner_depth=90,
                inner_height=225,
                thickness=3,
                kerf_mm=0.2,
                clearance_mm=0.15,
                slot_width=86,
                slot_height=18,
                slot_y_from_bottom=38,
                lid=False,
                labels=True,
                sheet_width=340,
            ),
        ),
        (
            "box_with_lid.svg",
            gen.BoxParams(
                preset="box_with_lid",
                inner_width=135,
                inner_depth=90,
                inner_height=225,
                thickness=3,
                kerf_mm=0.2,
                clearance_mm=0.15,
                lid=True,
                lid_height=30,
                lid_clearance=0.4,
                labels=True,
                sheet_width=340,
            ),
        ),
    ]

    for filename, params in examples:
        panels = gen.build_panels_for_preset(params)
        svg = gen.make_svg(
            panels,
            meta=params.__dict__,
            sheet_width=params.sheet_width,
            labels=params.labels,
            offset_kerf=params.offset_kerf,
            kerf_mm=params.kerf_mm,
        )
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
            f.write(svg)

    # Calibration plate
    gen.build_calibration_svg(
        thickness=3.0,
        kerf_mm=0.2,
        clearance_values=[-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20],
        out_path=os.path.join(out_dir, "calibration_mating_strips.svg"),
    )


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(__file__)))
