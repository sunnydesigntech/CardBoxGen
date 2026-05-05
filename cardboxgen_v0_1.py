#!/usr/bin/env python3
"""Backward-compatible CardBoxGen v0.1/v0.6 entry point.

The generator logic now lives in the ``cardboxgen`` package. This wrapper
preserves the historical script name and import surface for existing users.
"""

from __future__ import annotations

from cardboxgen.api import build_calibration_svg, build_panels_for_preset, generate_svg, generate_svg_with_warnings
from cardboxgen.cli import main
from cardboxgen.geometry import (
    Point,
    add,
    bbox_points,
    dot,
    fmt,
    is_axis_aligned_dir,
    mul,
    outward_normal_for_edge,
    polygon_area,
    polygon_to_path_with_tabs,
    polyline_to_path,
    sub,
    translate_points,
)
from cardboxgen.joints import (
    EdgeFamily,
    EdgeKey,
    FingerPlan,
    build_finger_plan,
    compute_finger_count,
    finger_edge_points,
    joint_depths_drawn,
)
from cardboxgen.models import BoxParams
from cardboxgen.panels import CutPath, EdgePair, Panel
from cardboxgen.svg import make_svg, offset_polygon_pyclipper, try_import_pyclipper
from cardboxgen.version import __version__

__all__ = [
    "__version__",
    "Point",
    "BoxParams",
    "CutPath",
    "Panel",
    "EdgePair",
    "EdgeFamily",
    "EdgeKey",
    "FingerPlan",
    "fmt",
    "add",
    "sub",
    "mul",
    "dot",
    "polyline_to_path",
    "polygon_to_path_with_tabs",
    "bbox_points",
    "polygon_area",
    "translate_points",
    "is_axis_aligned_dir",
    "outward_normal_for_edge",
    "joint_depths_drawn",
    "compute_finger_count",
    "build_finger_plan",
    "finger_edge_points",
    "build_panels_for_preset",
    "generate_svg",
    "generate_svg_with_warnings",
    "build_calibration_svg",
    "make_svg",
    "try_import_pyclipper",
    "offset_polygon_pyclipper",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
