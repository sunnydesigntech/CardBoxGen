from cardboxgen.fabrication import (
    KerfModel,
    drawn_slot_depth_for_target,
    drawn_slot_width_for_target,
    drawn_tab_depth_for_target,
    drawn_tab_width_for_target,
    final_slot_depth_from_drawn,
    final_slot_width_from_drawn,
    final_tab_depth_from_drawn,
    final_tab_width_from_drawn,
)


def test_kerf_full_width_sign_convention():
    kerf = 0.2
    assert KerfModel(kerf).burn_radius_mm == 0.1
    assert final_tab_width_from_drawn(10.2, kerf) == 10.0
    assert final_slot_width_from_drawn(9.8, kerf) == 10.0


def test_width_inverse_formulas():
    kerf = 0.18
    target = 12.0
    assert abs(final_tab_width_from_drawn(drawn_tab_width_for_target(target, kerf), kerf) - target) < 1e-9
    assert abs(final_slot_width_from_drawn(drawn_slot_width_for_target(target, kerf), kerf) - target) < 1e-9


def test_open_edge_depth_inverse_formulas():
    kerf = 0.2
    target_tab = 3.0
    target_slot = 3.15
    tab_drawn = drawn_tab_depth_for_target(target_tab, kerf)
    slot_drawn = drawn_slot_depth_for_target(target_slot, kerf)
    assert abs(final_tab_depth_from_drawn(tab_drawn, kerf) - target_tab) < 1e-9
    assert abs(final_slot_depth_from_drawn(slot_drawn, kerf) - target_slot) < 1e-9
