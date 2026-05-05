"""Argparse CLI for CardBoxGen."""

from __future__ import annotations

import argparse
import json
import sys

from .api import generate_svg
from .version import __version__


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate laser-cut SVG card boxes and mechanisms.")
    ap.add_argument("--version", action="store_true", help="Print version and exit.")
    ap.add_argument("--preset", "--template-id", dest="preset", default=None, help="Preset/template ID.")
    ap.add_argument("--variant", choices=["A", "B", "C"], default=None, help="Legacy variant alias if --preset is omitted.")
    ap.add_argument("--calibration", action="store_true", help="Generate calibration fit strips.")

    ap.add_argument("--inner-width", type=float, default=135.0)
    ap.add_argument("--inner-depth", type=float, default=90.0)
    ap.add_argument("--inner-height", type=float, default=80.0)
    ap.add_argument("--thickness", type=float, default=3.0)
    ap.add_argument("--kerf", type=float, default=0.2)
    ap.add_argument("--clearance", type=float, default=0.15)
    ap.add_argument("--finger-width", type=float, default=None)
    ap.add_argument("--min-fingers", type=int, default=3)

    ap.add_argument("--front-height", type=float, default=None)
    ap.add_argument("--scoop", action="store_true", default=False)
    ap.add_argument("--scoop-radius", type=float, default=22.0)
    ap.add_argument("--scoop-depth", type=float, default=16.0)
    ap.add_argument("--slot-width", type=float, default=80.0)
    ap.add_argument("--slot-height", type=float, default=18.0)
    ap.add_argument("--slot-y-from-bottom", type=float, default=35.0)
    ap.add_argument("--window-margin", type=float, default=12.0)
    ap.add_argument("--divider-count", "--divider-bays", dest="divider_count", type=int, default=3)

    ap.add_argument("--lid", action="store_true", default=True)
    ap.add_argument("--no-lid", dest="lid", action="store_false")
    ap.add_argument("--lid-height", type=float, default=25.0)
    ap.add_argument("--lid-clearance", type=float, default=0.4)

    ap.add_argument("--card-width", type=float, default=63.0)
    ap.add_argument("--card-height", type=float, default=88.0)
    ap.add_argument("--card-thickness", type=float, default=0.35)
    ap.add_argument("--capacity", type=int, default=60)
    ap.add_argument("--ramp-angle-deg", type=float, default=12.0)

    ap.add_argument("--max-piece", type=float, default=18.0)
    ap.add_argument("--irregular", action="store_true", default=False)
    ap.add_argument("--hopper-height", type=float, default=90.0)
    ap.add_argument("--depth-layers-total", type=int, default=8)
    ap.add_argument("--wheel-layers", type=int, default=3)
    ap.add_argument("--screw-diameter", type=float, default=3.2)
    ap.add_argument("--screw-margin", type=float, default=10.0)
    ap.add_argument("--axle-diameter", type=float, default=6.0)
    ap.add_argument("--add-feet", action="store_true", default=False)

    ap.add_argument("--sheet-width", type=float, default=340.0)
    ap.add_argument("--margin", type=float, default=10.0)
    ap.add_argument("--padding", type=float, default=12.0)
    ap.add_argument("--stroke", type=float, default=0.2)
    ap.add_argument("--no-labels", dest="labels", action="store_false", default=True)
    ap.add_argument("--offset-kerf", action="store_true", default=False)
    ap.add_argument("--holding-tabs", action="store_true", default=False)
    ap.add_argument("--tab-width", type=float, default=2.0)
    ap.add_argument("--clearance-values", default="-0.10,-0.05,0,0.05,0.10,0.15,0.20")

    ap.add_argument("--json", action="store_true", help="Print JSON result to stdout instead of status lines.")
    ap.add_argument("--out", required=False, default="out.svg", help="Output SVG path.")
    return ap.parse_args(argv)


def _variant_to_preset(variant: str | None) -> str:
    if variant == "A":
        return "tray_open_front"
    if variant == "B":
        return "window_front"
    if variant == "C":
        return "box_with_lid"
    return "tray_open_front"


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    preset = "calibration" if args.calibration else (args.preset or _variant_to_preset(args.variant))
    params = {
        "inner_w": args.inner_width,
        "inner_d": args.inner_depth,
        "inner_h": args.inner_height,
        "thickness": args.thickness,
        "kerf": args.kerf,
        "fit_clearance": args.clearance,
        "finger_w": args.finger_width,
        "min_fingers": args.min_fingers,
        "front_h": args.front_height,
        "scoop": args.scoop,
        "scoop_r": args.scoop_radius,
        "scoop_depth": args.scoop_depth,
        "slot_width": args.slot_width,
        "slot_height": args.slot_height,
        "slot_y_from_bottom": args.slot_y_from_bottom,
        "window_margin": args.window_margin,
        "divider_count": args.divider_count,
        "lid": args.lid,
        "lid_height": args.lid_height,
        "lid_clearance": args.lid_clearance,
        "card_w": args.card_width,
        "card_h": args.card_height,
        "card_t": args.card_thickness,
        "capacity": args.capacity,
        "ramp_angle_deg": args.ramp_angle_deg,
        "max_piece": args.max_piece,
        "irregular": args.irregular,
        "hopper_h": args.hopper_height,
        "depth_layers_total": args.depth_layers_total,
        "wheel_layers": args.wheel_layers,
        "screw_d": args.screw_diameter,
        "screw_margin": args.screw_margin,
        "axle_d": args.axle_diameter,
        "add_feet": args.add_feet,
        "max_row_width": args.sheet_width,
        "margin": args.margin,
        "gap": args.padding,
        "stroke_mm": args.stroke,
        "labels": args.labels,
        "offset_kerf": args.offset_kerf,
        "holding_tabs": args.holding_tabs,
        "tab_width_mm": args.tab_width,
    }
    if preset == "calibration":
        params["clearance_values"] = args.clearance_values
    result = generate_svg(preset, params)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(result["svg"])
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Wrote {args.out}")
        for w in result.get("warnings", []):
            print(f"{w['severity'].upper()} {w['code']}: {w['message']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
