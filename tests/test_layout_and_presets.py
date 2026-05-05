import re
import xml.etree.ElementTree as ET

from cardboxgen.api import build_design, generate_svg
from cardboxgen.geometry import polygon_area
from cardboxgen.layout import arrange_panels, has_overlaps


PRESETS = [
    "tray_open_front",
    "dispenser_slot_front",
    "window_front",
    "box_with_lid",
    "divider_rack",
    "card_shoe",
    "candy_machine_rotary_layered",
    "calibration",
]


def params_for(template_id):
    common = {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15}
    if template_id == "card_shoe":
        return {"card_w": 63, "card_h": 88, "card_t": 0.35, "capacity": 50, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15}
    if template_id == "candy_machine_rotary_layered":
        return {"max_piece": 18, "irregular": False, "hopper_h": 90, "depth_layers_total": 8, "wheel_layers": 3, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15, "screw_d": 3.2, "screw_margin": 10, "axle_d": 6}
    if template_id == "calibration":
        return {"thickness": 3, "kerf": 0.2}
    return common


def test_all_presets_generate_valid_svg_and_layers():
    for template_id in PRESETS:
        result = generate_svg(template_id, params_for(template_id))
        root = ET.fromstring(result["svg"])
        assert root.tag.endswith("svg")
        assert root.attrib["width"].endswith("mm")
        assert root.attrib["height"].endswith("mm")
        assert "viewBox" in root.attrib
        assert 'id="CUT"' in result["svg"]
        assert 'id="SCORE"' in result["svg"]
        assert 'id="ENGRAVE"' in result["svg"]


def test_all_presets_have_nonempty_panel_outlines_and_layout_no_overlap():
    for template_id in PRESETS:
        panels, warnings, meta = build_design(template_id, params_for(template_id))
        assert panels
        for panel in panels:
            assert len(panel.outline) >= 4
            assert abs(polygon_area(panel.outline)) > 1e-6
        placed, _, _ = arrange_panels(panels, sheet_width=340, margin=10, gap=12)
        assert not has_overlaps(placed)


def test_mating_edge_pairs_share_length_count_and_complement_masks():
    for template_id in ["tray_open_front", "dispenser_slot_front", "window_front", "box_with_lid", "divider_rack", "card_shoe"]:
        _, _, meta = build_design(template_id, params_for(template_id))
        for pair in meta.get("edge_pairs", []):
            assert pair["length"] > 0
            assert pair["count"] == len(pair["widths"])
            assert len(pair["tabs_a"]) == pair["count"]
            assert len(pair["tabs_b"]) == pair["count"]
            assert all(a is not b for a, b in zip(pair["tabs_a"], pair["tabs_b"]))
            assert abs(sum(pair["widths"]) - pair["length"]) < 1e-6


def test_parameter_sweep_preserves_requested_inner_dimensions():
    for w in [60, 90, 135]:
        for d in [50, 90]:
            for h in [40, 120]:
                result = generate_svg("tray_open_front", {"inner_w": w, "inner_d": d, "inner_h": h, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15})
                dims = result["meta"]["dimensions"]
                assert dims["inner"] == {"w": w, "d": d, "h": h}
                assert dims["outer"]["w"] == w + 6
                assert dims["outer"]["d"] == d + 6
                assert dims["outer"]["h"] == h + 3


def test_expected_cutout_features_are_present():
    checks = {
        "dispenser_slot_front": "draw_slot|cutout",
        "window_front": "view_window|cutout",
        "divider_rack": "divider_slot",
        "card_shoe": "draw_slot",
        "candy_machine_rotary_layered": "metering_pocket|wheel_cavity|screw_hole",
    }
    for template_id, pattern in checks.items():
        panels, _, _ = build_design(template_id, params_for(template_id))
        kinds = " ".join(c.kind for p in panels for c in p.cutouts)
        assert re.search(pattern, kinds)
