import math

import pytest

import cardboxgen_v0_1 as gen


def _edge_endpoints(points):
    if not points:
        return None
    return points[0], points[-1]


def test_finger_count_stable_small_length_change():
    # Small length change should not cause random flip-flopping.
    n1 = gen.compute_finger_count(100.0, 12.0, min_fingers=3)
    n2 = gen.compute_finger_count(100.2, 12.0, min_fingers=3)
    n3 = gen.compute_finger_count(99.9, 12.0, min_fingers=3)
    assert n1 == n2 == n3
    assert n1 % 2 == 1


def test_edge_pair_complementary_same_segment_count_and_endpoints():
    length = 123.0
    n = gen.compute_finger_count(length, 12.0, min_fingers=3)
    plan = gen.build_finger_plan(length, count=n, kerf_mm=0.2, clearance_mm=0.15, start_with_tab_on_a=True)

    start = (0.0, 0.0)
    dirv = (1, 0)
    normal = gen.outward_normal_for_edge(dirv)

    a_pts = gen.finger_edge_points(start, dirv, normal, plan, thickness=3.0, invert_tabs=False)
    b_pts = gen.finger_edge_points(start, dirv, normal, plan, thickness=3.0, invert_tabs=True)

    assert len(a_pts) == len(b_pts)

    # Both should end at the same baseline endpoint
    assert pytest.approx(a_pts[-1][0], abs=1e-6) == length
    assert pytest.approx(a_pts[-1][1], abs=1e-6) == 0.0
    assert pytest.approx(b_pts[-1][0], abs=1e-6) == length
    assert pytest.approx(b_pts[-1][1], abs=1e-6) == 0.0


def test_panel_outline_closed_non_empty():
    p = gen.BoxParams(
        preset="dispenser_slot_front",
        inner_width=135,
        inner_depth=90,
        inner_height=225,
        thickness=3,
        kerf_mm=0.2,
        clearance_mm=0.15,
        labels=False,
        lid=False,
    )
    panels = gen.build_panels_for_preset(p)
    assert panels
    for panel in panels:
        assert len(panel.outline) >= 4
        area = gen.polygon_area(panel.outline)
        assert not math.isclose(area, 0.0, abs_tol=1e-6)
