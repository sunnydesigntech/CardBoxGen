import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from assembly_oracle import assert_design_sound
from cardboxgen.validation import validate_template_params


@given(
    thickness=st.floats(min_value=1.0, max_value=6.0, allow_nan=False, allow_infinity=False),
    kerf=st.floats(min_value=0.05, max_value=0.45, allow_nan=False, allow_infinity=False),
    clearance=st.floats(min_value=0.0, max_value=0.40, allow_nan=False, allow_infinity=False),
    inner_w=st.floats(min_value=50.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    inner_d=st.floats(min_value=50.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    inner_h=st.floats(min_value=40.0, max_value=300.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20, deadline=None)
def test_tray_open_front_valid_domain_property(thickness, kerf, clearance, inner_w, inner_d, inner_h):
    if kerf >= thickness:
        return
    params = {
        "inner_w": inner_w,
        "inner_d": inner_d,
        "inner_h": inner_h,
        "thickness": thickness,
        "kerf": kerf,
        "fit_clearance": clearance,
        "scoop": False,
        "max_row_width": 500,
    }
    assume(not validate_template_params("tray_open_front", params).blocking)
    assert_design_sound("tray_open_front", params)


@pytest.mark.slow
def test_slow_deterministic_all_preset_sweep():
    for thickness in (2.0, 3.0, 5.0):
        for clearance in (0.0, 0.15, 0.35):
            common = {"inner_w": 120, "inner_d": 80, "inner_h": 70, "thickness": thickness, "kerf": 0.2, "fit_clearance": clearance, "max_row_width": 500}
            for template_id in ("tray_open_front", "dispenser_slot_front", "window_front", "box_with_lid", "divider_rack"):
                assert_design_sound(template_id, common)
