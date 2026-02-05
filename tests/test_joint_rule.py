def test_joint_depth_rule_matches_spec():
    # Spec: final_slot ≈ drawn_slot + kerf; target_final_slot = thickness + clearance
    # => drawn_slot = thickness + clearance − kerf
    from cardboxgen_v0_1 import joint_depths_drawn

    t = 3.0
    kerf = 0.2
    clearance = 0.2
    tab_d, slot_d = joint_depths_drawn(thickness=t, kerf_mm=kerf, clearance_mm=clearance)

    assert tab_d == t
    assert abs(slot_d - (t + clearance - kerf)) < 1e-9
