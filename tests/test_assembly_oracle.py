from assembly_oracle import assert_depth_model, assert_design_sound, assert_rectangular_tray_graph
from cardboxgen.api import generate_svg


VALID_PRESETS = {
    "tray_open_front": {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15},
    "dispenser_slot_front": {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15},
    "window_front": {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15},
    "box_with_lid": {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.4},
    "divider_rack": {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15, "divider_count": 4},
    "card_shoe": {"card_w": 63, "card_h": 88, "card_t": 0.35, "capacity": 60, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15},
    "candy_machine_rotary_layered": {"max_piece": 18, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.2, "screw_margin": 10, "screw_d": 3.2, "axle_d": 6, "depth_layers_total": 8, "wheel_layers": 3},
    "calibration": {"thickness": 3, "kerf": 0.2},
}


def test_assembly_oracle_all_presets():
    for template_id, params in VALID_PRESETS.items():
        assert_design_sound(template_id, params)
        result = generate_svg(template_id, params)
        assert_depth_model(result["meta"])


def test_labels_and_stroke_do_not_change_nominal_cut_metadata():
    base = generate_svg("tray_open_front", VALID_PRESETS["tray_open_front"])
    changed = generate_svg("tray_open_front", {**VALID_PRESETS["tray_open_front"], "labels": False, "stroke_mm": 0.8})
    assert base["meta"]["dimensions"] == changed["meta"]["dimensions"]
    assert base["meta"]["edge_pairs"] == changed["meta"]["edge_pairs"]


def test_open_tray_uses_explicit_rectangular_assembly_graph():
    result = generate_svg("tray_open_front", VALID_PRESETS["tray_open_front"])
    assert_rectangular_tray_graph(result["meta"])
