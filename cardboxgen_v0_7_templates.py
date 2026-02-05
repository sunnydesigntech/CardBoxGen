#!/usr/bin/env python3
"""
CardBoxGen v0.7 — Mechanism Templates (Expanded Prototype)

This file provides mechanism-first templates with validation:
- tray_open_front      (stacking access tray)
- divider_rack         (stacking access tray + slotted dividers)
- window_front         (storage box with window)
- card_shoe            (stacking cards, front-draw with ramp support)
- rotary_wheel         (flowing solids, rotary pocket wheel module)

Outputs: laser-cut SVG (mm units) with labelled parts laid out.
"""
from __future__ import annotations

import argparse, json, math, textwrap
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

Point = Tuple[float, float]

def fmt(n: float) -> str:
    return f"{n:.3f}".rstrip("0").rstrip(".")

def add(p: Point, q: Point) -> Point:
    return (p[0] + q[0], p[1] + q[1])

def mul(p: Point, s: float) -> Point:
    return (p[0] * s, p[1] * s)

def polyline_to_path(points: List[Point], close: bool = True) -> str:
    if not points:
        return ""
    d = [f"M {fmt(points[0][0])} {fmt(points[0][1])}"]
    for x, y in points[1:]:
        d.append(f"L {fmt(x)} {fmt(y)}")
    if close:
        d.append("Z")
    return " ".join(d)

def edge_points(start: Point, dirv: Point, normal_out: Point, length: float, *,
                jointed: bool, t: float, finger_w: float, phase: int) -> List[Point]:
    if length <= 0:
        return []
    if not jointed:
        return [add(start, mul(dirv, length))]

    n = max(3, int(round(length / max(1e-6, finger_w))))
    if n % 2 == 0:
        n += 1
    seg = length / n

    pts: List[Point] = []
    p = start
    for i in range(n):
        protrude = ((i + phase) % 2 == 0)
        off = mul(normal_out, t if protrude else -t)
        pts.append(add(p, off))
        p = add(p, mul(dirv, seg))
        pts.append(add(p, off))
        pts.append(p)
    return pts

def rect_with_fingers(w: float, h: float, *, t: float, finger_w: float,
                      joints: Dict[str, bool], phases: Dict[str, int]) -> List[Point]:
    p0 = (0.0, 0.0)
    pts = [p0]
    pts += edge_points(p0, (1, 0), (0, -1), w, jointed=joints.get("top", False), t=t, finger_w=finger_w, phase=phases.get("top", 0))
    p1 = (w, 0.0)
    pts += edge_points(p1, (0, 1), (1, 0), h, jointed=joints.get("right", False), t=t, finger_w=finger_w, phase=phases.get("right", 0))
    p2 = (w, h)
    pts += edge_points(p2, (-1, 0), (0, 1), w, jointed=joints.get("bottom", False), t=t, finger_w=finger_w, phase=phases.get("bottom", 0))
    p3 = (0.0, h)
    pts += edge_points(p3, (0, -1), (-1, 0), h, jointed=joints.get("left", False), t=t, finger_w=finger_w, phase=phases.get("left", 0))
    return pts

def bbox_points(points: List[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))

def panel_bbox(outline: List[Point]) -> Tuple[float, float]:
    x0, y0, x1, y1 = bbox_points(outline)
    return (x1 - x0, y1 - y0)

def rect_path(x: float, y: float, w: float, h: float) -> str:
    return f"M {fmt(x)} {fmt(y)} L {fmt(x+w)} {fmt(y)} L {fmt(x+w)} {fmt(y+h)} L {fmt(x)} {fmt(y+h)} Z"

def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = max(0.0, min(r, w/2, h/2))
    if r <= 0:
        return rect_path(x, y, w, h)
    return (
        f"M {fmt(x+r)} {fmt(y)} "
        f"L {fmt(x+w-r)} {fmt(y)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x+w)} {fmt(y+r)} "
        f"L {fmt(x+w)} {fmt(y+h-r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x+w-r)} {fmt(y+h)} "
        f"L {fmt(x+r)} {fmt(y+h)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y+h-r)} "
        f"L {fmt(x)} {fmt(y+r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x+r)} {fmt(y)} Z"
    )

def circle_path(cx: float, cy: float, r: float) -> str:
    return (
        f"M {fmt(cx+r)} {fmt(cy)} "
        f"A {fmt(r)} {fmt(r)} 0 1 0 {fmt(cx-r)} {fmt(cy)} "
        f"A {fmt(r)} {fmt(r)} 0 1 0 {fmt(cx+r)} {fmt(cy)} Z"
    )

def thumb_notch_path(w: float, y_top: float, radius: float, depth: float) -> str:
    cx = w / 2
    x0 = cx - radius
    x1 = cx + radius
    y0 = y_top
    y1 = y_top + depth
    return (
        f"M {fmt(x0)} {fmt(y0)} "
        f"L {fmt(x0)} {fmt(y1)} "
        f"A {fmt(radius)} {fmt(radius)} 0 0 0 {fmt(x1)} {fmt(y1)} "
        f"L {fmt(x1)} {fmt(y0)} Z"
    )

@dataclass
class Panel:
    name: str
    outline: List[Point]
    cutouts: List[str]
    labels: List[Tuple[str, Point]]

@dataclass
class WarningMsg:
    severity: str  # error|warn|info
    code: str
    message: str
    fix: str

def arrange_panels(panels: List[Panel], gap: float = 12.0, max_row_width: float = 340.0):
    placed = []
    x = y = 0.0
    row_h = 0.0
    total_w = total_h = 0.0
    for p in panels:
        bw, bh = panel_bbox(p.outline)
        if placed and (x + bw > max_row_width):
            x = 0.0
            y += row_h + gap
            row_h = 0.0
        placed.append((p, x, y))
        x += bw + gap
        row_h = max(row_h, bh)
        total_w = max(total_w, x)
        total_h = max(total_h, y + row_h)
    return placed, total_w + gap, total_h + gap

def svg_header(W: float, H: float) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(W)}mm" height="{fmt(H)}mm" viewBox="0 0 {fmt(W)} {fmt(H)}">
"""

def svg_footer() -> str:
    return "</svg>\n"

def make_svg(
    panels: List[Panel],
    meta: dict,
    *,
    max_row_width: float = 340.0,
    gap: float = 12.0,
    stroke_mm: float = 0.2,
    include_labels: bool = True,
) -> str:
    placed, W, H = arrange_panels(panels, gap=gap, max_row_width=max_row_width)
    meta_comment = "\n".join(textwrap.wrap(json.dumps(meta, ensure_ascii=False), width=120))
    out = [svg_header(W, H)]
    out.append(f"  <!-- meta: {meta_comment} -->\n")
    out.append(f'  <g id="CUT" fill="none" stroke="red" stroke-width="{fmt(float(stroke_mm))}">\n')
    for p, x, y in placed:
        out.append(f'    <g id="{p.name}" transform="translate({fmt(x)},{fmt(y)})">\n')
        out.append(f'      <path d="{polyline_to_path(p.outline, close=True)}"/>\n')
        for cd in p.cutouts:
            out.append(f'      <path d="{cd}"/>\n')
        out.append("    </g>\n")
    out.append("  </g>\n")
    if include_labels:
        out.append('  <g id="ENGRAVE" fill="black" font-family="Arial" font-size="4">\n')
        for p, x, y in placed:
            if p.labels:
                out.append(f'    <g transform="translate({fmt(x)},{fmt(y)})">\n')
                for txt, (tx, ty) in p.labels:
                    out.append(f'      <text x="{fmt(tx)}" y="{fmt(ty)}">{txt}</text>\n')
                out.append("    </g>\n")
        out.append("  </g>\n")
    out.append(svg_footer())
    return "".join(out)


def _warn_dicts(warns: List[WarningMsg]) -> List[dict]:
    return [w.__dict__.copy() for w in (warns or [])]


def generate_svg(template_id: str, params: dict) -> dict:
    """Public API for Pyodide integration.

    Returns a JSON-serializable dict:
      {"svg": str, "warnings": [{severity, code, message, fix}, ...], "meta": dict, "bundle_files": {}}
    """
    if not isinstance(params, dict):
        raise TypeError("params must be a dict")

    tid = str(template_id or "").strip()
    if not tid:
        raise ValueError("template_id is required")

    thickness = float(params.get("thickness", 3.0))
    kerf = float(params.get("kerf", 0.2))
    fit_clearance = float(params.get("fit_clearance", 0.15))
    finger_w = params.get("finger_w", None)
    finger_w = None if finger_w is None else float(finger_w)

    # Layout options (UI uses sheet width/padding-like fields).
    max_row_width = float(params.get("max_row_width", 340.0))
    gap = float(params.get("gap", 12.0))

    stroke_mm = float(params.get("stroke_mm", 0.2))
    include_labels = bool(params.get("labels", True))

    common = dict(thickness=thickness, kerf=kerf, fit_clearance=fit_clearance, finger_w=finger_w)

    if tid == "tray_open_front":
        panels, warns, meta = build_tray_open_front(
            inner_w=float(params.get("inner_w", 135.0)),
            inner_d=float(params.get("inner_d", 90.0)),
            inner_h=float(params.get("inner_h", 80.0)),
            front_h=float(params.get("front_h", 30.0)),
            scoop=bool(params.get("scoop", True)),
            scoop_r=float(params.get("scoop_r", 22.0)),
            scoop_depth=float(params.get("scoop_depth", 16.0)),
            **common,
        )
    elif tid == "divider_rack":
        panels, warns, meta = build_divider_rack(
            inner_w=float(params.get("inner_w", 135.0)),
            inner_d=float(params.get("inner_d", 90.0)),
            inner_h=float(params.get("inner_h", 80.0)),
            divider_count=int(params.get("divider_count", 3)),
            **common,
        )
    elif tid == "window_front":
        panels, warns, meta = build_window_front(
            inner_w=float(params.get("inner_w", 135.0)),
            inner_d=float(params.get("inner_d", 90.0)),
            inner_h=float(params.get("inner_h", 80.0)),
            window_margin=float(params.get("window_margin", 12.0)),
            **common,
        )
    elif tid == "card_shoe":
        panels, warns, meta = build_card_shoe_front_draw(
            card_w=float(params.get("card_w", 63.0)),
            card_h=float(params.get("card_h", 88.0)),
            card_t=float(params.get("card_t", 0.35)),
            capacity=int(params.get("capacity", 60)),
            ramp_angle_deg=float(params.get("ramp_angle_deg", 12.0)),
            **common,
        )
    elif tid == "rotary_wheel":
        panels, warns, meta = build_rotary_wheel_candy(
            max_piece=float(params.get("max_piece", 18.0)),
            irregular=bool(params.get("irregular", False)),
            axle_d=float(params.get("axle_d", 3.2)),
            **common,
        )
    elif tid == "candy_machine_rotary_layered":
        panels, warns, meta = build_candy_machine_rotary_layered(
            max_piece=float(params.get("max_piece", 18.0)),
            irregular=bool(params.get("irregular", False)),
            hopper_h=float(params.get("hopper_h", 120.0)),
            depth_layers_total=int(params.get("depth_layers_total", 8)),
            wheel_layers=int(params.get("wheel_layers", 3)),
            screw_d=float(params.get("screw_d", 3.0)),
            screw_margin=float(params.get("screw_margin", 10.0)),
            axle_d=float(params.get("axle_d", 6.0)),
            add_feet=bool(params.get("add_feet", False)),
            **common,
        )
    else:
        raise ValueError(f"Unknown template_id: {tid}")

    svg = make_svg(
        panels,
        meta,
        max_row_width=max_row_width,
        gap=gap,
        stroke_mm=stroke_mm,
        include_labels=include_labels,
    )

    return {
        "svg": svg,
        "warnings": _warn_dicts(warns),
        "meta": meta,
        "bundle_files": {},
    }

def mk_panel_rect(name: str, w: float, h: float, *, t: float, finger_w: float,
                  joints: Dict[str, bool], phases: Dict[str, int], cutouts=None, labels=None) -> Panel:
    outline = rect_with_fingers(w, h, t=t, finger_w=finger_w, joints=joints, phases=phases)
    return Panel(name=name, outline=outline, cutouts=cutouts or [], labels=labels or [(name, (w*0.35, h*0.55))])

def drawn_slot_width(thickness: float, clearance: float, kerf: float) -> float:
    """
    The slot should end up ~ thickness + clearance after cutting.
    So the drawn slot is reduced by kerf (approx): t + clearance - kerf.
    """
    return max(0.2, thickness + clearance - kerf)

# ---------------------- Template: Open-front tray ----------------------

def build_tray_open_front(*, inner_w: float, inner_d: float, inner_h: float,
                          front_h: float = 30.0,
                          scoop: bool = True, scoop_r: float = 22.0, scoop_depth: float = 16.0,
                          thickness: float = 3.0, kerf: float = 0.2, fit_clearance: float = 0.15,
                          finger_w: Optional[float] = None) -> Tuple[List[Panel], List[WarningMsg], dict]:
    t = thickness
    finger_w = finger_w if finger_w is not None else max(10.0, 3.0 * t)

    W_out = inner_w + 2*t
    D_out = inner_d + 2*t

    phases0 = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    phases1 = {"top": 1, "right": 1, "bottom": 1, "left": 1}

    warns: List[WarningMsg] = []
    if front_h >= inner_h:
        warns.append(WarningMsg("warn", "TRAY_FRONT_TOO_TALL",
                                "Front height is close to or above side height; tray may not be 'open front'.",
                                "Reduce front_h."))

    panels: List[Panel] = []

    # Bottom (jointed all around)
    panels.append(mk_panel_rect("BOTTOM", W_out, D_out, t=t, finger_w=finger_w,
                               joints={"top": True, "right": True, "bottom": True, "left": True},
                               phases=phases0,
                               labels=[("BOTTOM", (W_out*0.4, D_out*0.55))]))

    # Left/Right walls (depth x height), open top
    side_j = {"top": False, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("LEFT", D_out, inner_h, t=t, finger_w=finger_w, joints=side_j, phases=phases1))
    panels.append(mk_panel_rect("RIGHT", D_out, inner_h, t=t, finger_w=finger_w, joints=side_j, phases=phases1))

    # Back wall (width x height)
    back_j = {"top": False, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("BACK", W_out, inner_h, t=t, finger_w=finger_w, joints=back_j, phases=phases0))

    # Front lip (width x front_h) with optional scoop cutout
    cutouts = []
    if scoop:
        # Scoop notch in top edge area (implemented as a notch cutout starting at y=front_h - scoop_depth)
        y_top = max(2.0, front_h - scoop_depth)
        cutouts.append(thumb_notch_path(W_out, y_top=y_top, radius=min(scoop_r, W_out*0.25), depth=min(scoop_depth, front_h-2.0)))
    panels.append(mk_panel_rect("FRONT_LIP", W_out, front_h, t=t, finger_w=finger_w,
                               joints={"top": False, "right": True, "bottom": True, "left": True},
                               phases=phases0, cutouts=cutouts,
                               labels=[("FRONT_LIP", (W_out*0.32, front_h*0.65))]))

    meta = {
        "template": "TRAY_OPEN_FRONT_v0.7_proto",
        "inputs": {"inner_w": inner_w, "inner_d": inner_d, "inner_h": inner_h, "front_h": front_h},
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance},
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta

# ---------------------- Template: Divider rack ----------------------

def build_divider_rack(*, inner_w: float, inner_d: float, inner_h: float,
                       divider_count: int = 3,
                       thickness: float = 3.0, kerf: float = 0.2, fit_clearance: float = 0.15,
                       finger_w: Optional[float] = None) -> Tuple[List[Panel], List[WarningMsg], dict]:
    t = thickness
    finger_w = finger_w if finger_w is not None else max(10.0, 3.0 * t)
    slot_w = drawn_slot_width(t, fit_clearance, kerf)
    tab_depth = max(6.0, 2.0*t)

    W_out = inner_w + 2*t
    D_out = inner_d + 2*t

    phases0 = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    phases1 = {"top": 1, "right": 1, "bottom": 1, "left": 1}

    warns: List[WarningMsg] = []
    if divider_count < 2:
        warns.append(WarningMsg("error", "DIV_TOO_FEW", "divider_count must be >= 2.", "Increase divider_count."))

    # Bottom with slots
    bottom = rect_with_fingers(W_out, D_out, t=t, finger_w=finger_w,
                               joints={"top": True, "right": True, "bottom": True, "left": True},
                               phases=phases0)
    bottom_cutouts = []

    # Slots positioned evenly across width, inside clearance from edges
    margin = 10.0
    usable = inner_w - 2*margin
    if usable <= (divider_count-1)*slot_w:
        warns.append(WarningMsg("error", "DIV_TOO_TIGHT",
                                "Not enough width for divider slots with current divider_count.",
                                "Reduce divider_count or increase inner_w."))
    else:
        # slots located at interior x positions: margin + k*gap
        gap = usable / divider_count
        for i in range(1, divider_count):
            x = t + margin + i*gap - slot_w/2
            y = t + 6.0
            h = inner_d - 12.0
            bottom_cutouts.append(rect_path(x, y, slot_w, h))

    panels: List[Panel] = []
    panels.append(Panel("BOTTOM", bottom, bottom_cutouts, [("BOTTOM", (W_out*0.4, D_out*0.55))]))

    # Walls like open-front tray but full front
    side_j = {"top": False, "right": True, "bottom": True, "left": True}
    back_j = {"top": False, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("LEFT", D_out, inner_h, t=t, finger_w=finger_w, joints=side_j, phases=phases1))
    panels.append(mk_panel_rect("RIGHT", D_out, inner_h, t=t, finger_w=finger_w, joints=side_j, phases=phases1))
    panels.append(mk_panel_rect("BACK", W_out, inner_h, t=t, finger_w=finger_w, joints=back_j, phases=phases0))
    panels.append(mk_panel_rect("FRONT", W_out, inner_h*0.6, t=t, finger_w=finger_w, joints=back_j, phases=phases0,
                               labels=[("FRONT (LOW)", (W_out*0.28, inner_h*0.35))]))

    # Divider panels with bottom tabs that fit the slots (glue optional)
    div_h = inner_h - 2.0
    div_w = inner_d
    tab_w = slot_w
    # Divider outline: rectangle plus one tab centred at bottom
    def divider_outline() -> List[Point]:
        x0,y0 = 0.0, 0.0
        x1,y1 = div_w, div_h
        cx = div_w/2
        # tab at bottom protruding down by tab_depth
        pts = [
            (x0,y0),
            (x1,y0),
            (x1,y1),
            (x0,y1),
        ]
        # This outline is plain; tabs are added as protrusion by redefining bottom edge
        # We'll construct a closed polyline with tab.
        tb0 = (cx - tab_w/2, y0)
        tb1 = (cx + tab_w/2, y0)
        out = [
            (x0,y0),
            tb0,
            (tb0[0], y0 - tab_depth),
            (tb1[0], y0 - tab_depth),
            tb1,
            (x1,y0),
            (x1,y1),
            (x0,y1),
        ]
        return out

    for i in range(divider_count-1):
        panels.append(Panel(f"DIVIDER_{i+1}", divider_outline(), [], [(f"DIVIDER_{i+1}", (div_w*0.2, div_h*0.6))]))

    # Required features: slots + dividers
    if not bottom_cutouts:
        warns.append(WarningMsg("error", "DIV_NO_SLOTS", "Bottom divider slots missing.", "Ensure bottom slots are generated."))
    if not any(p.name.startswith("DIVIDER_") for p in panels):
        warns.append(WarningMsg("error", "DIV_NO_DIVIDERS", "Divider parts missing.", "Generate divider parts."))

    meta = {
        "template": "DIVIDER_RACK_v0.7_proto",
        "inputs": {"inner_w": inner_w, "inner_d": inner_d, "inner_h": inner_h, "divider_count": divider_count},
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance, "drawn_slot_w": slot_w},
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta

# ---------------------- Template: Window front box ----------------------

def build_window_front(*, inner_w: float, inner_d: float, inner_h: float,
                       window_margin: float = 12.0,
                       thickness: float = 3.0, kerf: float = 0.2, fit_clearance: float = 0.15,
                       finger_w: Optional[float] = None) -> Tuple[List[Panel], List[WarningMsg], dict]:
    t = thickness
    finger_w = finger_w if finger_w is not None else max(10.0, 3.0 * t)

    W_out = inner_w + 2*t
    D_out = inner_d + 2*t
    H = inner_h

    phases0 = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    phases1 = {"top": 1, "right": 1, "bottom": 1, "left": 1}

    warns: List[WarningMsg] = []

    panels: List[Panel] = []
    panels.append(mk_panel_rect("BOTTOM", W_out, D_out, t=t, finger_w=finger_w,
                               joints={"top": True, "right": True, "bottom": True, "left": True},
                               phases=phases0))
    wall_j = {"top": True, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("LEFT", D_out, H, t=t, finger_w=finger_w, joints={"top": True,"right": True,"bottom": True,"left": True}, phases=phases1))
    panels.append(mk_panel_rect("RIGHT", D_out, H, t=t, finger_w=finger_w, joints={"top": True,"right": True,"bottom": True,"left": True}, phases=phases1))
    panels.append(mk_panel_rect("BACK", W_out, H, t=t, finger_w=finger_w, joints={"top": True,"right": True,"bottom": True,"left": True}, phases=phases0))
    # FRONT with window cutout
    win_w = max(10.0, W_out - 2*window_margin)
    win_h = max(10.0, H - 2*window_margin)
    cutouts = [rounded_rect_path(window_margin, window_margin, win_w, win_h, r=8.0)]
    panels.append(mk_panel_rect("FRONT", W_out, H, t=t, finger_w=finger_w, joints={"top": True,"right": True,"bottom": True,"left": True}, phases=phases0,
                               cutouts=cutouts,
                               labels=[("FRONT (WINDOW)", (W_out*0.22, H*0.55))]))
    # TOP
    panels.append(mk_panel_rect("TOP", W_out, D_out, t=t, finger_w=finger_w,
                               joints={"top": True, "right": True, "bottom": True, "left": True},
                               phases=phases1,
                               labels=[("TOP", (W_out*0.45, D_out*0.55))]))
    meta = {
        "template": "WINDOW_FRONT_v0.7_proto",
        "inputs": {"inner_w": inner_w, "inner_d": inner_d, "inner_h": inner_h},
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance},
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta

# ---------------------- Template: Card shoe (front draw) ----------------------

def build_card_shoe_front_draw(*, card_w: float, card_h: float, card_t: float,
                               capacity: int,
                               thickness: float = 3.0, kerf: float = 0.2, fit_clearance: float = 0.15,
                               finger_w: Optional[float] = None,
                               ramp_angle_deg: float = 12.0,
                               include_stabilizers: bool = True) -> Tuple[List[Panel], List[WarningMsg], dict]:
    t = thickness
    finger_w = finger_w if finger_w is not None else max(10.0, 3.0 * t)

    W_in = card_w + 2.0
    D_in = card_h + 1.5
    H_stack = capacity * card_t
    H_in = H_stack + 10.0

    W_out = W_in + 2 * t
    D_out = D_in + 2 * t
    H = H_in

    slot_h = max(1.0, min(2.0, card_t + 0.6))
    slot_w = card_w * 0.85
    lip_h = 10.0

    warns: List[WarningMsg] = []
    if slot_h < card_t + 0.3:
        warns.append(WarningMsg("error", "CS_SLOT_TOO_SMALL",
                                f"Draw slot height {slot_h:.2f}mm is too small for card thickness {card_t:.2f}mm (jam risk).",
                                "Increase slot height (advanced) or verify card thickness input."))
    if slot_h > card_t + 2.5:
        warns.append(WarningMsg("warn", "CS_SLOT_TOO_TALL",
                                f"Draw slot height {slot_h:.2f}mm is much larger than card thickness {card_t:.2f}mm (multi-card risk).",
                                "Reduce slot height or increase retention lip height."))

    if H / max(1e-6, W_in) > 2.0 and not include_stabilizers:
        warns.append(WarningMsg("warn", "CS_TIPPY",
                                f"Box is tall relative to width (H/W≈{H/W_in:.2f}); may tip during pulling.",
                                "Enable stabilisers or increase base width."))

    phases0 = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    phases1 = {"top": 1, "right": 1, "bottom": 1, "left": 1}

    panels: List[Panel] = []

    panels.append(mk_panel_rect("BOTTOM", W_out, D_out, t=t, finger_w=finger_w,
                               joints={"top": True, "right": True, "bottom": True, "left": True},
                               phases=phases0,
                               labels=[("BOTTOM", (W_out * 0.4, D_out * 0.55))]))

    side_j = {"top": False, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("LEFT", D_out, H, t=t, finger_w=finger_w, joints=side_j, phases=phases1))
    panels.append(mk_panel_rect("RIGHT", D_out, H, t=t, finger_w=finger_w, joints=side_j, phases=phases1))

    back_j = {"top": False, "right": True, "bottom": True, "left": True}
    panels.append(mk_panel_rect("BACK", W_out, H, t=t, finger_w=finger_w, joints=back_j, phases=phases0))

    cutouts = []
    win_margin_x = max(8.0, (W_out - slot_w) / 2 - 4.0)
    win_w = W_out - 2 * win_margin_x
    win_h = max(30.0, min(H * 0.45, 70.0))
    win_x = win_margin_x
    win_y = lip_h + 6.0
    cutouts.append(rounded_rect_path(win_x, win_y, win_w, win_h, r=6.0))

    slot_x = (W_out - slot_w) / 2
    slot_y = max(2.0, lip_h - slot_h - 1.0)
    cutouts.append(rect_path(slot_x, slot_y, slot_w, slot_h))

    notch_r = min(10.0, slot_w * 0.18)
    cutouts.append(thumb_notch_path(W_out, y_top=lip_h + 1.0, radius=notch_r, depth=min(10.0, notch_r)))

    panels.append(mk_panel_rect("FRONT", W_out, H, t=t, finger_w=finger_w, joints=back_j, phases=phases0,
                               cutouts=cutouts,
                               labels=[("FRONT (DRAW)", (W_out * 0.32, H * 0.55))]))

    ramp_w = W_in
    ramp_d = D_in
    ramp_outline = [(0, 0), (ramp_w, 0), (ramp_w, ramp_d), (0, ramp_d)]
    panels.append(Panel("RAMP_PLATE", ramp_outline, [], [("RAMP_PLATE", (ramp_w * 0.25, ramp_d * 0.55))]))

    rise = max(8.0, min(H * 0.6, D_in * math.tan(math.radians(ramp_angle_deg))))
    block_d = 25.0
    for i in range(2):
        outline = [(0, 0), (block_d, 0), (block_d, rise), (0, rise)]
        panels.append(Panel(f"RAMP_BLOCK_{i+1}", outline, [], [(f"RAMP_BLOCK_{i+1}", (2.0, rise * 0.55))]))
    bar_w = ramp_w
    bar_h = min(12.0, rise)
    outline = [(0, 0), (bar_w, 0), (bar_w, bar_h), (0, bar_h)]
    panels.append(Panel("RAMP_BACK_BAR", outline, [], [("RAMP_BACK_BAR", (bar_w * 0.25, bar_h * 0.7))]))

    if include_stabilizers:
        stab_w = W_out * 0.8
        stab_d = 14.0
        outline = [(0, 0), (stab_w, 0), (stab_w, stab_d), (0, stab_d)]
        panels.append(Panel("STABILISER_1", outline, [], [("STABILISER_1", (stab_w * 0.25, stab_d * 0.7))]))
        panels.append(Panel("STABILISER_2", outline, [], [("STABILISER_2", (stab_w * 0.25, stab_d * 0.7))]))

    if not any(p.name == "RAMP_PLATE" for p in panels):
        warns.append(WarningMsg("error", "CS_NO_RAMP", "Internal support (ramp) is missing.", "Add ramp parts."))
    if not any(p.name == "FRONT" and len(p.cutouts) >= 2 for p in panels):
        warns.append(WarningMsg("error", "CS_NO_FRONT_FEATURES", "Front draw cutouts are missing.", "Ensure draw slot + window exist."))

    meta = {
        "template": "CARD_SHOE_FRONT_DRAW_v0.7_proto",
        "inputs": {"card_w": card_w, "card_h": card_h, "card_t": card_t, "capacity": capacity},
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance},
        "derived": {"W_in": W_in, "D_in": D_in, "H_in": H_in, "slot_h": slot_h, "slot_w": slot_w, "lip_h": lip_h, "ramp_rise": rise},
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta

# ---------------------- Template: Rotary wheel candy ----------------------

def build_rotary_wheel_candy(*, max_piece: float, irregular: bool,
                             thickness: float = 3.0, kerf: float = 0.2, fit_clearance: float = 0.15,
                             finger_w: Optional[float] = None,
                             axle_d: float = 3.2) -> Tuple[List[Panel], List[WarningMsg], dict]:
    p = max_piece
    pocket_d = p + (2.0 if irregular else 1.0)
    pocket_r = pocket_d / 2

    pocket_count = max(6, int(round(2 * math.pi * (pocket_d * 1.5) / max(6.0, pocket_d))))
    if pocket_count % 2 == 1:
        pocket_count += 1

    wheel_r = max(30.0, (pocket_count * pocket_d / (2 * math.pi)) * 1.35)
    wheel_d = 2 * wheel_r

    chute_w = pocket_d + 2.0
    chute_h = max(10.0, pocket_d * 0.8)

    warns: List[WarningMsg] = []
    if chute_w <= p:
        warns.append(WarningMsg("error", "RW_CHUTE_TOO_NARROW",
                                f"Chute width {chute_w:.2f}mm is <= max piece {p:.2f}mm (bridging).",
                                "Increase chute width or reduce max_piece input."))

    wall_between = (2 * math.pi * wheel_r / pocket_count) - pocket_d
    if wall_between < 2.0:
        warns.append(WarningMsg("error", "RW_POCKET_WALL_TOO_THIN",
                                f"Wall between pockets ≈{wall_between:.2f}mm (<2.0mm).",
                                "Increase wheel diameter or reduce pocket count."))

    ring_outer_r = wheel_r + pocket_d + 6.0
    ring_inner_r = wheel_r + 2.0
    plate_w = (ring_outer_r * 2) + 10.0
    plate_h = plate_w

    cx = plate_w / 2
    cy = plate_h / 2

    panels: List[Panel] = []

    base_outline = [(0, 0), (plate_w, 0), (plate_w, plate_h), (0, plate_h)]
    base_cutouts = [
        circle_path(cx, cy, axle_d / 2),
        rounded_rect_path(cx - chute_w/2, plate_h - chute_h - 6.0, chute_w, chute_h, r=2.0),
    ]
    panels.append(Panel("BASE_PLATE", base_outline, base_cutouts, [("BASE_PLATE", (plate_w * 0.33, plate_h * 0.55))]))

    segs = 96
    wheel_outline = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        wheel_outline.append((wheel_r * math.cos(ang) + wheel_r, wheel_r * math.sin(ang) + wheel_r))
    wheel_cutouts = [circle_path(wheel_r, wheel_r, axle_d/2)]
    pocket_ring_r = wheel_r - pocket_d * 0.85
    for i in range(pocket_count):
        ang = 2 * math.pi * i / pocket_count
        px = wheel_r + pocket_ring_r * math.cos(ang)
        py = wheel_r + pocket_ring_r * math.sin(ang)
        wheel_cutouts.append(circle_path(px, py, pocket_r))
    panels.append(Panel("WHEEL", wheel_outline, wheel_cutouts, [("WHEEL", (wheel_r * 0.6, wheel_r * 1.05))]))

    def donut(name: str) -> Panel:
        outline = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            outline.append((ring_outer_r * math.cos(ang) + ring_outer_r, ring_outer_r * math.sin(ang) + ring_outer_r))
        cutouts = [
            circle_path(ring_outer_r, ring_outer_r, ring_inner_r),
            circle_path(ring_outer_r, ring_outer_r, axle_d/2),
        ]
        return Panel(name, outline, cutouts, [(name, (ring_outer_r * 0.55, ring_outer_r * 1.05))])

    panels.append(donut("SPACER_RING_1"))
    panels.append(donut("SPACER_RING_2"))

    top_cutouts = [
        circle_path(cx, cy, ring_inner_r),
        circle_path(cx, cy, axle_d/2),
    ]
    panels.append(Panel("TOP_PLATE", base_outline, top_cutouts, [("TOP_PLATE", (plate_w * 0.36, plate_h * 0.55))]))

    knob_r = max(12.0, axle_d * 2.5)
    knob_outline = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        knob_outline.append((knob_r * math.cos(ang) + knob_r, knob_r * math.sin(ang) + knob_r))
    panels.append(Panel("KNOB", knob_outline, [circle_path(knob_r, knob_r, axle_d/2)], [("KNOB", (knob_r * 0.5, knob_r * 1.05))]))

    if not any(p.name == "WHEEL" for p in panels):
        warns.append(WarningMsg("error", "RW_NO_WHEEL", "Wheel part missing.", "Generate wheel part."))

    meta = {
        "template": "ROTARY_WHEEL_CANDY_v0.7_proto",
        "inputs": {"max_piece": max_piece, "irregular": irregular},
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance, "finger_w": finger_w, "axle_d": axle_d},
        "derived": {"pocket_d": pocket_d, "pocket_count": pocket_count, "wheel_d": wheel_d, "chute_w": chute_w, "plate_w": plate_w},
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta


def _circle_outline(r: float, *, segs: int = 96) -> List[Point]:
    segs = max(12, int(segs))
    pts: List[Point] = []
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        pts.append((r * math.cos(ang) + r, r * math.sin(ang) + r))
    return pts


def build_candy_machine_rotary_layered(
    *,
    max_piece: float,
    irregular: bool,
    hopper_h: float,
    depth_layers_total: int,
    wheel_layers: int,
    screw_d: float,
    screw_margin: float,
    axle_d: float,
    add_feet: bool = False,
    thickness: float = 3.0,
    kerf: float = 0.2,
    fit_clearance: float = 0.15,
    finger_w: Optional[float] = None,
) -> Tuple[List[Panel], List[WarningMsg], dict]:
    """Layered rotary wheel candy machine.

    Sandwich construction:
      FRONT_ACRYLIC + (HOPPER_SPACER_xN) + (WHEEL_SPACER_xM) + BACK_PLATE
    Plus moving parts: WHEEL + KNOB (+ optional FEET).

    Notes:
    - This is not a finger-jointed box; plates are held with screws.
    - depth_layers_total is total spacer layers (not counting FRONT/BACK plates).
    - wheel_layers is how many of those spacer layers form the wheel chamber.
    """

    t = float(thickness)
    p = float(max_piece)
    hopper_h = float(hopper_h)
    screw_d = float(screw_d)
    screw_margin = float(screw_margin)
    axle_d = float(axle_d)

    warns: List[WarningMsg] = []

    if p <= 0:
        warns.append(WarningMsg("error", "CM_MAX_PIECE_INVALID", "max_piece must be > 0.", "Increase max_piece."))
    if hopper_h < 40.0:
        warns.append(WarningMsg("warn", "CM_HOPPER_LOW", "Hopper height is quite small; capacity may be low.", "Increase hopper_h."))

    if depth_layers_total < 2:
        warns.append(WarningMsg("error", "CM_LAYERS_TOO_FEW", "depth_layers_total must be >= 2.", "Set depth_layers_total to 8 (typical for 3mm boards)."))
    if wheel_layers < 1:
        warns.append(WarningMsg("error", "CM_WHEEL_LAYERS_TOO_FEW", "wheel_layers must be >= 1.", "Set wheel_layers to 3 (typical)."))
    if depth_layers_total >= 2 and wheel_layers >= depth_layers_total:
        warns.append(WarningMsg("error", "CM_LAYER_SPLIT_INVALID", "wheel_layers must be less than depth_layers_total.", "Make sure there is at least 1 hopper spacer layer."))

    hopper_layers = max(0, int(depth_layers_total) - int(wheel_layers))
    wheel_layers = int(wheel_layers)
    depth_layers_total = int(depth_layers_total)

    # Derived pocket + wheel geometry.
    safety = 2.0 if irregular else 1.0
    pocket_d = p + safety
    pocket_r = pocket_d / 2.0

    pocket_count = max(8, int(round(2 * math.pi * (pocket_d * 1.6) / max(10.0, pocket_d))))
    if pocket_count % 2 == 1:
        pocket_count += 1

    wheel_r = max(28.0, (pocket_count * pocket_d / (2 * math.pi)) * 1.25)
    wheel_d = 2 * wheel_r

    # Chute/feed windows. Keep intentionally generous.
    feed_w = max(pocket_d * 0.85, p * 1.2)
    feed_h = max(10.0, pocket_d * 0.9)

    chute_w = pocket_d + (3.0 if irregular else 2.0)
    chute_h = max(12.0, pocket_d * 1.1)

    # Validation: chute and pocket walls.
    if chute_w <= p * 1.10:
        warns.append(
            WarningMsg(
                "error",
                "CM_CHUTE_TOO_NARROW",
                f"Chute width {chute_w:.2f}mm is too close to max piece {p:.2f}mm (bridging risk).",
                "Increase chute width by increasing max_piece safety (tick irregular) or increase depth/scale.",
            )
        )

    wall_between = (2 * math.pi * wheel_r / pocket_count) - pocket_d
    if wall_between < 2.0:
        warns.append(
            WarningMsg(
                "error",
                "CM_POCKET_WALL_TOO_THIN",
                f"Wall between pockets ≈{wall_between:.2f}mm (<2.0mm).",
                "Reduce pocket count (increase wheel diameter) or reduce max_piece.",
            )
        )

    # Plate sizing.
    side_wall = max(10.0, screw_margin + screw_d)
    wheel_clear = max(2.0, fit_clearance + 0.6)
    wheel_cavity_r = wheel_r + wheel_clear

    # Place wheel in lower half; hopper above.
    chute_bottom_margin = max(14.0, screw_margin + screw_d + 4.0)
    wheel_top_y = side_wall + max(12.0, hopper_h * 0.20)
    cy = wheel_top_y + wheel_cavity_r

    plate_w = max(wheel_cavity_r * 2 + side_wall * 2, 140.0)
    plate_h = max(cy + wheel_cavity_r + chute_bottom_margin, wheel_d + hopper_h + side_wall * 2)
    cx = plate_w / 2.0

    # Hopper cavity rectangle (in spacer layers).
    hopper_x = side_wall
    hopper_y = side_wall
    hopper_w = plate_w - 2 * side_wall
    hopper_h_cut = max(40.0, min(hopper_h, plate_h - side_wall * 2 - wheel_cavity_r * 0.6))

    # Feed window (connect hopper to wheel top).
    feed_x = cx - feed_w / 2
    feed_y = hopper_y + hopper_h_cut - (feed_h * 0.6)

    # Exit window (wheel bottom to chute).
    exit_w = max(chute_w, pocket_d * 0.9)
    exit_h = max(10.0, pocket_d * 0.8)
    exit_x = cx - exit_w / 2
    exit_y = (cy + wheel_cavity_r) - (exit_h * 0.4)

    # Chute channel to front opening.
    chute_x = cx - chute_w / 2
    chute_y = exit_y + exit_h * 0.7
    chute_y = min(chute_y, plate_h - chute_bottom_margin - chute_h)

    # Dispense opening on front acrylic.
    opening_w = max(chute_w + 6.0, 24.0)
    opening_h = max(14.0, chute_h * 0.8)
    opening_x = cx - opening_w / 2
    opening_y = plate_h - chute_bottom_margin - opening_h

    # Screw hole pattern (4 corners).
    hole_r = max(0.6, screw_d / 2.0)
    screw_pts = [
        (screw_margin, screw_margin),
        (plate_w - screw_margin, screw_margin),
        (screw_margin, plate_h - screw_margin),
        (plate_w - screw_margin, plate_h - screw_margin),
    ]

    # Ensure screw margin is sane.
    if screw_margin < 6.0:
        warns.append(WarningMsg("warn", "CM_SCREW_MARGIN_SMALL", "Screw margin is small; holes may be too close to edge.", "Increase screw_margin to ~10–12mm."))
    if screw_margin > min(plate_w, plate_h) / 3:
        warns.append(WarningMsg("warn", "CM_SCREW_MARGIN_LARGE", "Screw margin is large; plates may be oversized.", "Reduce screw_margin."))

    panels: List[Panel] = []

    plate_outline = [(0.0, 0.0), (plate_w, 0.0), (plate_w, plate_h), (0.0, plate_h)]

    def screw_holes() -> List[str]:
        return [circle_path(x, y, hole_r) for (x, y) in screw_pts]

    # FRONT acrylic: screw holes + axle + dispense opening.
    front_cutouts = []
    front_cutouts += screw_holes()
    front_cutouts.append(circle_path(cx, cy, axle_d / 2.0))
    front_cutouts.append(rounded_rect_path(opening_x, opening_y, opening_w, opening_h, r=3.0))
    panels.append(Panel("FRONT_ACRYLIC", plate_outline, front_cutouts, [("FRONT_ACRYLIC", (plate_w * 0.22, plate_h * 0.55))]))

    # BACK plate: screw holes + axle.
    back_cutouts = []
    back_cutouts += screw_holes()
    back_cutouts.append(circle_path(cx, cy, axle_d / 2.0))
    panels.append(Panel("BACK_PLATE", plate_outline, back_cutouts, [("BACK_PLATE", (plate_w * 0.30, plate_h * 0.55))]))

    # Hopper spacer layers: hollow hopper cavity, plus screw + axle clearance.
    hopper_cutouts = []
    hopper_cutouts += screw_holes()
    hopper_cutouts.append(circle_path(cx, cy, axle_d / 2.0 + 0.6))
    hopper_cutouts.append(rounded_rect_path(hopper_x, hopper_y, hopper_w, hopper_h_cut, r=6.0))

    for i in range(hopper_layers):
        panels.append(
            Panel(
                f"HOPPER_SPACER_{i+1}",
                plate_outline,
                hopper_cutouts,
                [(f"HOPPER_{i+1}", (plate_w * 0.22, plate_h * 0.58))],
            )
        )

    # Wheel spacer layers: wheel cavity + feed window + exit window + chute channel.
    wheel_cutouts = []
    wheel_cutouts += screw_holes()
    wheel_cutouts.append(circle_path(cx, cy, axle_d / 2.0 + 0.8))
    wheel_cutouts.append(circle_path(cx, cy, wheel_cavity_r))
    wheel_cutouts.append(rounded_rect_path(feed_x, feed_y, feed_w, feed_h, r=3.0))
    wheel_cutouts.append(rounded_rect_path(exit_x, exit_y, exit_w, exit_h, r=3.0))
    wheel_cutouts.append(rounded_rect_path(chute_x, chute_y, chute_w, chute_h, r=3.0))

    for i in range(wheel_layers):
        panels.append(
            Panel(
                f"WHEEL_SPACER_{i+1}",
                plate_outline,
                wheel_cutouts,
                [(f"WHEEL_{i+1}", (plate_w * 0.22, plate_h * 0.62))],
            )
        )

    # Wheel part (pocket wheel).
    wheel_outline = _circle_outline(wheel_r)
    pocket_ring_r = wheel_r - pocket_d * 0.85
    wheel_cutouts2 = [circle_path(wheel_r, wheel_r, axle_d / 2.0)]
    for i in range(pocket_count):
        ang = 2 * math.pi * i / pocket_count
        px = wheel_r + pocket_ring_r * math.cos(ang)
        py = wheel_r + pocket_ring_r * math.sin(ang)
        wheel_cutouts2.append(circle_path(px, py, pocket_r))
    panels.append(Panel("WHEEL", wheel_outline, wheel_cutouts2, [("WHEEL", (wheel_r * 0.45, wheel_r * 1.05))]))

    # Knob.
    knob_r = max(14.0, axle_d * 2.2)
    knob_outline = _circle_outline(knob_r)
    panels.append(Panel("KNOB", knob_outline, [circle_path(knob_r, knob_r, axle_d / 2.0)], [("KNOB", (knob_r * 0.55, knob_r * 1.05))]))

    # Optional feet.
    if add_feet:
        foot_w = max(30.0, plate_w * 0.28)
        foot_h = 12.0
        foot_outline = [(0.0, 0.0), (foot_w, 0.0), (foot_w, foot_h), (0.0, foot_h)]
        panels.append(Panel("FOOT_1", foot_outline, [], [("FOOT_1", (2.0, foot_h * 0.7))]))
        panels.append(Panel("FOOT_2", foot_outline, [], [("FOOT_2", (2.0, foot_h * 0.7))]))

    # Required parts checks.
    if not any(p.name == "WHEEL" for p in panels):
        warns.append(WarningMsg("error", "CM_NO_WHEEL", "Wheel part missing.", "Generate wheel part."))
    if hopper_layers <= 0:
        warns.append(WarningMsg("error", "CM_NO_HOPPER_LAYERS", "No hopper spacer layers were generated.", "Increase depth_layers_total or reduce wheel_layers."))

    meta = {
        "template": "CANDY_MACHINE_ROTARY_LAYERED_v0.7_proto",
        "inputs": {
            "max_piece": max_piece,
            "irregular": irregular,
            "hopper_h": hopper_h,
            "depth_layers_total": depth_layers_total,
            "wheel_layers": wheel_layers,
            "screw_d": screw_d,
            "screw_margin": screw_margin,
            "axle_d": axle_d,
            "add_feet": add_feet,
        },
        "fabrication": {"thickness": thickness, "kerf": kerf, "fit_clearance": fit_clearance, "finger_w": finger_w},
        "derived": {
            "pocket_d": pocket_d,
            "pocket_count": pocket_count,
            "wheel_d": wheel_d,
            "chute_w": chute_w,
            "plate_w": plate_w,
            "plate_h": plate_h,
            "hopper_layers": hopper_layers,
        },
        "warnings": [w.__dict__ for w in warns],
    }
    return panels, warns, meta

# ---------------------- CLI ----------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", choices=["tray_open_front", "divider_rack", "window_front", "card_shoe", "rotary_wheel"], required=True)
    ap.add_argument("--out", required=True, help="Output SVG path")

    ap.add_argument("--thickness", type=float, default=3.0)
    ap.add_argument("--kerf", type=float, default=0.2)
    ap.add_argument("--fit", type=float, default=0.15)

    # Common box/tray params
    ap.add_argument("--inner_w", type=float, default=100.0)
    ap.add_argument("--inner_d", type=float, default=100.0)
    ap.add_argument("--inner_h", type=float, default=100.0)

    # Tray params
    ap.add_argument("--front_h", type=float, default=30.0)
    ap.add_argument("--no_scoop", action="store_true")

    # Divider params
    ap.add_argument("--divider_count", type=int, default=3)

    # Window params
    ap.add_argument("--window_margin", type=float, default=12.0)

    # Card shoe params
    ap.add_argument("--card_w", type=float, default=63.0)
    ap.add_argument("--card_h", type=float, default=88.0)
    ap.add_argument("--card_t", type=float, default=0.35)
    ap.add_argument("--capacity", type=int, default=120)
    ap.add_argument("--ramp_angle", type=float, default=12.0)

    # Rotary params
    ap.add_argument("--max_piece", type=float, default=12.0)
    ap.add_argument("--irregular", action="store_true")
    ap.add_argument("--axle_d", type=float, default=3.2)

    args = ap.parse_args()

    common = dict(thickness=args.thickness, kerf=args.kerf, fit_clearance=args.fit)

    if args.template == "tray_open_front":
        panels, warns, meta = build_tray_open_front(
            inner_w=args.inner_w, inner_d=args.inner_d, inner_h=args.inner_h,
            front_h=args.front_h, scoop=(not args.no_scoop),
            **common
        )
    elif args.template == "divider_rack":
        panels, warns, meta = build_divider_rack(
            inner_w=args.inner_w, inner_d=args.inner_d, inner_h=args.inner_h,
            divider_count=args.divider_count,
            **common
        )
    elif args.template == "window_front":
        panels, warns, meta = build_window_front(
            inner_w=args.inner_w, inner_d=args.inner_d, inner_h=args.inner_h,
            window_margin=args.window_margin,
            **common
        )
    elif args.template == "card_shoe":
        panels, warns, meta = build_card_shoe_front_draw(
            card_w=args.card_w, card_h=args.card_h, card_t=args.card_t, capacity=args.capacity,
            ramp_angle_deg=args.ramp_angle,
            **common
        )
    else:
        panels, warns, meta = build_rotary_wheel_candy(
            max_piece=args.max_piece, irregular=args.irregular, axle_d=args.axle_d,
            **common
        )

    svg = make_svg(panels, meta)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)

    errs = [w for w in warns if w.severity == "error"]
    if errs:
        print("EXPORT SHOULD BE BLOCKED (errors):")
        for w in errs:
            print("-", w.code, w.message, "| fix:", w.fix)
    else:
        if warns:
            print("Warnings:")
            for w in warns:
                print("-", w.severity, w.code, w.message, "| fix:", w.fix)
        print("OK")

if __name__ == "__main__":
    main()
