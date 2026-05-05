"""Independent-ish geometry checks for generated CardBoxGen designs."""

from __future__ import annotations

import math
import re
from typing import Iterable, List, Sequence, Tuple

from cardboxgen.api import build_design
from cardboxgen.fabrication import final_slot_depth_from_drawn, final_tab_depth_from_drawn
from cardboxgen.geometry import Point, bbox_points, polygon_area
from cardboxgen.layout import arrange_panels, has_overlaps
from cardboxgen.validation import validate_template_params


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if abs(o1) < 1e-9 or abs(o2) < 1e-9 or abs(o3) < 1e-9 or abs(o4) < 1e-9:
        return False
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def assert_no_self_intersections(points: Sequence[Point]) -> None:
    ring = list(points)
    assert len(ring) >= 4
    edges = list(zip(ring, ring[1:] + ring[:1]))
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if abs(i - j) <= 1 or {i, j} == {0, len(edges) - 1}:
                continue
            if a in (c, d) or b in (c, d):
                continue
            assert not _segments_intersect(a, b, c, d), f"self intersection between edges {i} and {j}"


def _numbers_from_path(path_d: str) -> List[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", path_d)]


def assert_cutouts_contained(panels, *, min_margin: float = 0.0) -> None:
    for panel in panels:
        x0, y0, x1, y1 = bbox_points(panel.outline)
        for cutout in panel.cutouts:
            if cutout.kind in {"width_fit_slot"}:
                continue
            cut_bbox = cutout.bbox()
            if cut_bbox is not None:
                cx0, cy0, cx1, cy1 = cut_bbox
                assert cx0 >= x0 - 1e-6
                assert cx1 <= x1 + 1e-6
                assert cy0 >= y0 - 1e-6
                assert cy1 <= y1 + 1e-6
                continue
            nums = _numbers_from_path(cutout.to_svg_d())
            if len(nums) < 4:
                continue
            xs = nums[0::2]
            ys = nums[1::2]
            # Arc flags can add harmless 0/1 values. This check is intentionally
            # a bounding guard, not a full SVG path evaluator.
            assert min(xs) >= x0 - 1e-6
            assert max(xs) <= x1 + 1e-6
            assert min(ys) >= y0 - 1e-6
            assert max(ys) <= y1 + 1e-6


def assert_edge_pair_fit(meta: dict, *, tolerance: float = 0.18) -> None:
    for pair in meta.get("edge_pairs", []):
        assert pair["length"] > 0
        assert pair["count"] == len(pair["widths"])
        assert pair["count"] == len(pair["tabs_a"]) == len(pair["tabs_b"])
        assert all(a is not b for a, b in zip(pair["tabs_a"], pair["tabs_b"]))
        assert pair.get("finger_plan_id") == pair["id"]
        assert len(pair["drawn_widths_a"]) == pair["count"]
        assert len(pair["drawn_widths_b"]) == pair["count"]
        assert abs(sum(pair["drawn_widths_a"]) - pair["length"]) < 1e-6
        assert abs(sum(pair["drawn_widths_b"]) - pair["length"]) < 1e-6
        assert abs(sum(pair["widths"]) - pair["length"]) < 1e-6
        target_clearance = float(pair["target_clearance"])
        finals_a = pair["final_widths_a"]
        finals_b = pair["final_widths_b"]
        for fa, fb, is_tab_a in zip(finals_a, finals_b, pair["tabs_a"]):
            clearance = (fb - fa) if is_tab_a else (fa - fb)
            assert abs(clearance - target_clearance) <= tolerance


def assert_design_sound(template_id: str, params: dict) -> None:
    validation = validate_template_params(template_id, params)
    assert not validation.blocking, validation.to_dict()
    panels, warnings, meta = build_design(validation.normalized_params["template_id"], validation.normalized_params)
    assert not any(w.severity == "error" for w in warnings)
    assert meta["exportable"] is True
    assert_edge_pair_fit(meta)
    for panel in panels:
        assert abs(polygon_area(panel.outline)) > 1e-6
        assert all(math.isfinite(x) and math.isfinite(y) for x, y in panel.outline)
        assert_no_self_intersections(panel.outline)
    assert_cutouts_contained(panels)
    placed, _, _ = arrange_panels(panels, sheet_width=params.get("max_row_width", 340), margin=params.get("margin", 10), gap=params.get("gap", 12))
    assert not has_overlaps(placed)
    dims = meta.get("dimensions")
    if dims and {"inner_w", "inner_d", "inner_h"}.issubset(validation.normalized_params):
        assert dims["inner"]["w"] == validation.normalized_params["inner_w"]
        assert dims["inner"]["d"] == validation.normalized_params["inner_d"]
        assert dims["inner"]["h"] == validation.normalized_params["inner_h"]


def assert_depth_model(meta: dict) -> None:
    fit = meta["validation"]["computed_limits"]["fit_model"]
    kerf = meta["validation"]["computed_limits"]["kerf_full_width_mm"]
    assert abs(final_tab_depth_from_drawn(fit["drawn_tab_depth"], kerf) - fit["target_final_tab_depth"]) < 1e-9
    assert abs(final_slot_depth_from_drawn(fit["drawn_slot_depth"], kerf) - fit["target_final_slot_depth"]) < 1e-9
