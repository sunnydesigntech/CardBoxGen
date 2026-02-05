import xml.etree.ElementTree as ET


def test_svg_is_valid_xml(tmp_path):
    # Smoke test: generator should output parseable XML.
    from cardboxgen_v0_1 import BoxParams, build_panels_for_preset, make_svg

    p = BoxParams(
        preset="tray_open_front",
        inner_width=135,
        inner_depth=90,
        inner_height=225,
        thickness=3,
        kerf_mm=0.2,
        clearance_mm=0.1,
        labels=True,
        sheet_width=340,
    )
    panels = build_panels_for_preset(p)
    svg = make_svg(
        panels,
        meta=p.__dict__,
        sheet_width=p.sheet_width,
        labels=p.labels,
        offset_kerf=False,
        kerf_mm=p.kerf_mm,
        layout_margin_mm=p.layout_margin_mm,
        layout_padding_mm=p.layout_padding_mm,
        stroke_mm=p.stroke_mm,
        holding_tabs=p.holding_tabs,
        tab_width_mm=p.tab_width_mm,
    )

    out = tmp_path / "out.svg"
    out.write_text(svg, encoding="utf-8")
    ET.parse(str(out))
