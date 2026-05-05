"""Independent-ish geometry checks for generated CardBoxGen designs."""

from __future__ import annotations

import math
import re
from typing import Iterable, List, Sequence, Tuple

from cardboxgen.api import build_design
from cardboxgen.fabrication import final_slot_depth_from_drawn, final_tab_depth_from_drawn
from cardboxgen.geometry import Point, bbox_points, dot, polygon_area, sub
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


def assert_assembly_graph_sound(meta: dict) -> None:
    graph = meta.get("assembly_graph")
    if not graph:
        return

    panels = graph.get("panels", [])
    edge_by_ref = {}
    for panel in panels:
        panel_id = panel["id"]
        assert panel["width"] > 0
        assert panel["height"] > 0
        for edge in panel.get("edges", []):
            key = (panel_id, edge["id"])
            assert key not in edge_by_ref, f"duplicate edge metadata: {key}"
            edge_by_ref[key] = edge
            if edge.get("joint_pair_id") is None:
                assert edge["role"] == "flat", f"exterior edge accidentally fingered: {key}"
            else:
                assert edge["role"] in {"tabbed", "slotted"}, f"mating edge has invalid role: {key}"

    partner_count = {}
    seen_pair_ids = set()
    for pair in graph.get("joint_pairs", []):
        pair_id = pair["id"]
        assert pair_id not in seen_pair_ids
        seen_pair_ids.add(pair_id)
        assert pair.get("finger_plan_id") == pair_id
        assert pair["length"] > 0
        assert pair["count"] >= 3 and pair["count"] % 2 == 1
        assert pair["count"] == len(pair["widths"])
        assert abs(sum(pair["widths"]) - pair["length"]) < 1e-6

        a = pair["a"]
        b = pair["b"]
        a_key = (a["panel"], a["edge"])
        b_key = (b["panel"], b["edge"])
        assert a_key in edge_by_ref, f"missing first edge metadata: {a_key}"
        assert b_key in edge_by_ref, f"missing second edge metadata: {b_key}"
        assert a_key != b_key
        partner_count[a_key] = partner_count.get(a_key, 0) + 1
        partner_count[b_key] = partner_count.get(b_key, 0) + 1

        a_edge = edge_by_ref[a_key]
        b_edge = edge_by_ref[b_key]
        assert a_edge["joint_pair_id"] == pair_id
        assert b_edge["joint_pair_id"] == pair_id
        assert a_edge["role"] != "flat"
        assert b_edge["role"] != "flat"
        assert abs((a_edge["length"] - a_edge["offset_start"] - a_edge["offset_end"]) - pair["length"]) < 1e-6
        assert abs((b_edge["length"] - b_edge["offset_start"] - b_edge["offset_end"]) - pair["length"]) < 1e-6

        assert len(pair["tabs_a"]) == len(pair["tabs_b"]) == pair["count"]
        assert all(x != y for x, y in zip(pair["tabs_a"], pair["tabs_b"]))
        assert pair["tabs_a_local"] == (_reverse(pair["tabs_a"]) if a.get("reverse") else pair["tabs_a"])
        assert pair["tabs_b_local"] == (_reverse(pair["tabs_b"]) if b.get("reverse") else pair["tabs_b"])

        assert pair["nominal_boundaries"][0] == 0.0
        assert abs(pair["nominal_boundaries"][-1] - pair["length"]) < 1e-6
        assert len(pair["nominal_boundaries"]) == pair["count"] + 1
        assert len(pair["drawn_widths_a"]) == len(pair["drawn_widths_b"]) == pair["count"]
        assert len(pair["drawn_boundaries_a"]) == len(pair["drawn_boundaries_b"]) == pair["count"] + 1
        assert abs(pair["drawn_boundaries_a"][-1] - pair["length"]) < 1e-6
        assert abs(pair["drawn_boundaries_b"][-1] - pair["length"]) < 1e-6

    for key, count in partner_count.items():
        assert count == 1, f"mating edge does not have exactly one partner: {key}"


def assert_clean_reserved_corner_zones(panels, meta: dict) -> None:
    graph = meta.get("assembly_graph")
    if not graph:
        return
    panel_by_name = {panel.name: panel for panel in panels}
    max_depth = 0.0
    for pair in graph.get("joint_pairs", []):
        max_depth = max(max_depth, float(pair.get("thickness") or 0) + float(pair.get("target_clearance") or 0) + float(pair.get("kerf_full_width_mm") or 0))
    max_depth = max(max_depth, 1.0)

    for panel_meta in graph.get("panels", []):
        panel = panel_by_name.get(panel_meta["id"])
        if panel is None:
            continue
        for edge in panel_meta.get("edges", []):
            start = tuple(edge["start"])
            dirv = tuple(edge["dir"])
            normal = (dirv[1], -dirv[0])
            length = float(edge["length"])
            start_clear = float(edge.get("offset_start") or 0)
            end_clear = float(edge.get("offset_end") or 0)
            if start_clear <= 0 and end_clear <= 0:
                continue
            for point in panel.outline:
                rel = sub(point, start)
                x = dot(rel, dirv)
                y = dot(rel, normal)
                if abs(y) > max_depth + 1e-6:
                    continue
                if -1e-6 <= x < start_clear - 1e-6:
                    assert abs(y) < 1e-6 or abs(x) < 1e-6, f"corner artifact near {panel.name}.{edge['id']} start: {(x, y)}"
                if length - end_clear + 1e-6 < x <= length + 1e-6:
                    assert abs(y) < 1e-6 or abs(x - length) < 1e-6, f"corner artifact near {panel.name}.{edge['id']} end: {(x, y)}"


def assert_rectangular_tray_graph(meta: dict) -> None:
    graph = meta.get("assembly_graph")
    assert graph, "rectangular box/tray templates must expose assembly_graph metadata"
    expected = {
        ("BOTTOM", "back", "BACK", "bottom"),
        ("BOTTOM", "front", "FRONT", "bottom"),
        ("BOTTOM", "left", "LEFT", "bottom"),
        ("BOTTOM", "right", "RIGHT", "bottom"),
        ("BACK", "left", "LEFT", "back"),
        ("BACK", "right", "RIGHT", "back"),
        ("FRONT", "left", "LEFT", "front"),
        ("FRONT", "right", "RIGHT", "front"),
    }
    actual = {(p["a"]["panel"], p["a"]["edge"], p["b"]["panel"], p["b"]["edge"]) for p in graph.get("joint_pairs", [])}
    assert expected.issubset(actual)


def _reverse(values):
    return list(reversed(values))


def assert_design_sound(template_id: str, params: dict) -> None:
    validation = validate_template_params(template_id, params)
    assert not validation.blocking, validation.to_dict()
    panels, warnings, meta = build_design(validation.normalized_params["template_id"], validation.normalized_params)
    assert not any(w.severity == "error" for w in warnings)
    assert meta["exportable"] is True
    assert_edge_pair_fit(meta)
    assert_assembly_graph_sound(meta)
    assert_clean_reserved_corner_zones(panels, meta)
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
