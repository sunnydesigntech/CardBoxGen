def test_joint_depth_rule_matches_spec():
    from cardboxgen.fabrication import final_slot_depth_from_drawn, final_tab_depth_from_drawn
    from cardboxgen_v0_1 import joint_depths_drawn

    t = 3.0
    kerf = 0.2
    clearance = 0.2
    tab_d, slot_d = joint_depths_drawn(thickness=t, kerf_mm=kerf, clearance_mm=clearance)

    assert abs(tab_d - (t + kerf)) < 1e-9
    assert abs(slot_d - (t + clearance - kerf)) < 1e-9
    assert abs(final_tab_depth_from_drawn(tab_d, kerf) - t) < 1e-9
    assert abs(final_slot_depth_from_drawn(slot_d, kerf) - (t + clearance)) < 1e-9


def test_width_compensation_normalizes_to_exact_edge_length():
    from cardboxgen.joints import build_finger_plan

    plan = build_finger_plan(101.0, count=9, kerf_mm=0.2, clearance_mm=0.15, start_with_tab_on_a=True)
    a = plan.drawn_widths_for_side(kerf_mm=0.2, clearance_mm=0.15, invert=False)
    b = plan.drawn_widths_for_side(kerf_mm=0.2, clearance_mm=0.15, invert=True)

    assert abs(sum(a) - 101.0) < 1e-9
    assert abs(sum(b) - 101.0) < 1e-9
    assert a != b
    assert plan.tabs_mask_for_a() == [not x for x in plan.complement_mask()]
