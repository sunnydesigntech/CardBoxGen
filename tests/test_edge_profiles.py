from cardboxgen.joints import build_finger_plan
from cardboxgen.panels import (
    EdgePair,
    EdgeRole,
    JointRenderParams,
    PanelEdge,
    PanelSpec,
    build_panel_outline,
    build_rect_panel_spec,
    compose_panel_outline,
    edge_profile_from_panel_edge,
    make_finger_edge_profile,
    render_panel_from_spec,
)
from cardboxgen.joints import EdgeKey


def _assert_no_duplicate_or_zero_segments(points):
    for a, b in zip(points, points[1:]):
        assert a != b


def _assert_reserved_zone_clear(profile):
    c0 = profile.corner_clearance_start
    c1 = profile.corner_clearance_end
    eps = 1e-9
    for x, y in profile.points:
        if x < c0 - eps:
            assert abs(y) < eps
        if x > profile.length - c1 + eps:
            assert abs(y) < eps
    for x in profile.transition_xs:
        assert x >= c0 - eps
        assert x <= profile.length - c1 + eps


def test_finger_edge_profile_is_local_bounded_and_corner_free():
    plan = build_finger_plan(50, count=5, start_with_tab_on_a=True)
    profile = make_finger_edge_profile(
        length=70,
        plan=plan,
        role=EdgeRole.TABBED,
        thickness=3,
        kerf_mm=0.2,
        clearance_mm=0.15,
        invert_tabs=False,
        corner_clearance_start=10,
        corner_clearance_end=10,
        finger_plan_id="test_pair",
    )
    assert profile.points[0] == (0.0, 0.0)
    assert profile.points[-1] == (70.0, 0.0)
    assert all(0 <= x <= 70 for x, _ in profile.points)
    _assert_no_duplicate_or_zero_segments(profile.points)
    _assert_reserved_zone_clear(profile)


def test_reversed_slotted_edge_profile_keeps_same_reserved_zone():
    plan = build_finger_plan(45, count=5, start_with_tab_on_a=True)
    profile = make_finger_edge_profile(
        length=65,
        plan=plan,
        role=EdgeRole.SLOTTED,
        thickness=3,
        kerf_mm=0.2,
        clearance_mm=0.15,
        invert_tabs=True,
        reverse_plan=True,
        corner_clearance_start=8,
        corner_clearance_end=12,
        finger_plan_id="test_pair",
    )
    assert profile.points[0] == (0.0, 0.0)
    assert profile.points[-1] == (65.0, 0.0)
    _assert_no_duplicate_or_zero_segments(profile.points)
    _assert_reserved_zone_clear(profile)


def test_composing_four_flat_edges_is_exact_rectangle():
    spec = build_rect_panel_spec("RECT", 80, 50)
    panel = render_panel_from_spec(spec, joint_params=JointRenderParams(3, 0.2, 0.15), edge_pairs={})
    assert panel.outline == [(0.0, 0.0), (80.0, 0.0), (80.0, 50.0), (0.0, 50.0)]


def test_one_fingered_edge_has_clean_nominal_corners():
    spec = build_rect_panel_spec("ONE", 80, 50)
    plan = build_finger_plan(60, count=5, start_with_tab_on_a=True)
    pair = EdgePair(
        id="top_pair",
        family="test",
        a=EdgeKey("ONE", "top"),
        b=EdgeKey("OTHER", "bottom"),
        length=60,
        plan=plan,
    )
    spec.edges[0].finger_pair_id = "top_pair"
    spec.edges[0].role = EdgeRole.TABBED
    spec.edges[0].joint_offset_start = 10
    spec.edges[0].joint_offset_end = 10
    outline = build_panel_outline(spec, joint_params=JointRenderParams(3, 0.2, 0.15), edge_pairs={"top_pair": pair})
    profile = outline.edges["top"]
    assert profile.points[0] == (0.0, 0.0)
    assert profile.points[-1] == (80.0, 0.0)
    _assert_reserved_zone_clear(profile)
    panel = render_panel_from_spec(spec, joint_params=JointRenderParams(3, 0.2, 0.15), edge_pairs={"top_pair": pair})
    assert panel.outline[0] == (0.0, 0.0)
    assert (80.0, 0.0) in panel.outline


def test_two_adjacent_fingered_edges_do_not_create_corner_block():
    spec = PanelSpec(
        name="ADJ",
        width=80,
        height=60,
        edges=[
            PanelEdge("top", (0, 0), (1, 0), 80, "top_pair", False, False, EdgeRole.TABBED, 10, 10),
            PanelEdge("right", (80, 0), (0, 1), 60, "right_pair", False, False, EdgeRole.TABBED, 10, 10),
            PanelEdge("bottom", (80, 60), (-1, 0), 80),
            PanelEdge("left", (0, 60), (0, -1), 60),
        ],
    )
    top_pair = EdgePair("top_pair", "test", EdgeKey("ADJ", "top"), EdgeKey("OTHER", "bottom"), 60, build_finger_plan(60, count=5))
    right_pair = EdgePair("right_pair", "test", EdgeKey("ADJ", "right"), EdgeKey("OTHER", "left"), 40, build_finger_plan(40, count=5))
    params = JointRenderParams(3, 0.2, 0.15)
    outline = build_panel_outline(spec, joint_params=params, edge_pairs={"top_pair": top_pair, "right_pair": right_pair})
    pts = compose_panel_outline(spec, outline)
    _assert_no_duplicate_or_zero_segments(pts)

    # In the top-right reserved corner square, only the nominal connector is allowed.
    for x, y in pts:
        in_corner_x = 70 < x < 83.3
        in_corner_y = -3.3 < y < 10
        if in_corner_x and in_corner_y:
            assert abs(y) < 1e-9 or abs(x - 80) < 1e-9
