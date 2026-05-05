"""Validation and parameter normalization for CardBoxGen templates."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .fabrication import (
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
from .joints import compute_finger_count
from .models import ValidationResult, WarningMsg

SUPPORTED_TEMPLATES = {
    "tray_open_front",
    "dispenser_slot_front",
    "window_front",
    "box_with_lid",
    "divider_rack",
    "card_shoe",
    "candy_machine_rotary_layered",
    "calibration",
}

ALIASES = {
    "card_shoe_front_draw": "card_shoe",
    "candy_rotary_wheel": "candy_machine_rotary_layered",
    "rotary_wheel": "candy_machine_rotary_layered",
}


def _msg(severity: str, code: str, message: str, fix: str, field: Optional[str] = None) -> WarningMsg:
    return WarningMsg(severity, code, message, fix, field=field)


def _num(params: Dict[str, Any], *keys: str, default: float) -> float:
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return float(params[key])
    return float(default)


def _int(params: Dict[str, Any], *keys: str, default: int) -> int:
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return int(float(params[key]))
    return int(default)


def _bool(params: Dict[str, Any], *keys: str, default: bool = False) -> bool:
    for key in keys:
        if key in params and params[key] is not None:
            value = params[key]
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)
    return bool(default)


def _maybe_num(params: Dict[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return float(params[key])
    return None


def _clearance_values(params: Dict[str, Any]) -> List[float]:
    raw = params.get("clearance_values")
    if raw is None:
        return [-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20]
    if isinstance(raw, str):
        return [float(x.strip()) for x in raw.split(",") if x.strip()]
    if isinstance(raw, Iterable):
        return [float(x) for x in raw]
    return [-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20]


def _template(template_id: str, params: Dict[str, Any], messages: List[WarningMsg]) -> str:
    tid = str(template_id or params.get("template_id") or params.get("preset") or "tray_open_front").strip()
    if tid in ALIASES:
        new_tid = ALIASES[tid]
        messages.append(_msg("warn", "TEMPLATE_ALIAS", f"Template '{tid}' is deprecated; using '{new_tid}'.", f"Use template_id '{new_tid}'.", "template_id"))
        tid = new_tid
    if tid not in SUPPORTED_TEMPLATES:
        messages.append(_msg("error", "UNKNOWN_TEMPLATE", f"Unknown template_id '{tid}'.", f"Use one of: {', '.join(sorted(SUPPORTED_TEMPLATES))}.", "template_id"))
    return tid


def _normalize_common(params: Dict[str, Any], messages: List[WarningMsg]) -> Dict[str, Any]:
    t = _num(params, "thickness", default=3.0)
    kerf = _num(params, "kerf", "kerf_mm", default=0.2)
    clearance = _num(params, "fit_clearance", "clearance", "clearance_mm", default=0.15)
    min_feature = _num(params, "min_feature_width", "min_feature_width_mm", default=max(2.0, t))
    min_web = _num(params, "min_web_mm", default=max(t, min_feature))
    finger_w = _maybe_num(params, "finger_w", "finger_width")
    min_fingers = _int(params, "min_fingers", default=3)
    sheet_width = _num(params, "max_row_width", "sheet_width", default=340.0)
    margin = _num(params, "margin", "layout_margin_mm", default=10.0)
    gap = _num(params, "gap", "layout_padding_mm", default=12.0)
    stroke = _num(params, "stroke_mm", default=0.2)

    if t <= 0:
        messages.append(_msg("error", "THICKNESS_INVALID", f"Thickness {t:g} mm is not positive.", "Measure the material and enter thickness > 0.", "thickness"))
    if kerf < 0:
        messages.append(_msg("error", "KERF_NEGATIVE", f"Kerf {kerf:g} mm is negative.", "Use 0 if unknown, then cut calibration strips.", "kerf"))
    if t > 0 and kerf >= t:
        messages.append(_msg("error", "KERF_TOO_LARGE", f"Kerf {kerf:g} mm is greater than or equal to thickness {t:g} mm.", "Check units; kerf should be full cut width, usually much smaller than thickness.", "kerf"))
    if clearance < 0:
        messages.append(_msg("error", "CLEARANCE_NEGATIVE", f"Clearance {clearance:g} mm is negative.", "Use clearance >= 0 and tune fit with calibration strips.", "fit_clearance"))
    if min_fingers < 3:
        messages.append(_msg("error", "MIN_FINGERS_TOO_LOW", "Finger count must be at least 3.", "Set min_fingers to an odd value >= 3.", "min_fingers"))
    if min_fingers % 2 == 0:
        messages.append(_msg("error", "MIN_FINGERS_EVEN", f"min_fingers {min_fingers} is even.", "Use an odd min_fingers value such as 3, 5, 7, 9, or 11.", "min_fingers"))
    for field in ("finger_count_outer", "finger_count_vertical"):
        if field in params and params[field] not in (None, ""):
            explicit = int(float(params[field]))
            if explicit < 3 or explicit % 2 == 0:
                messages.append(_msg("error", "EXPLICIT_FINGER_COUNT_INVALID", f"{field}={explicit} is not an odd count >= 3.", "Use an odd explicit finger count >= 3 or leave it blank.", field))
    if finger_w is not None and finger_w < max(t, min_feature):
        messages.append(_msg("error", "FINGER_WIDTH_TOO_SMALL", f"Target finger width {finger_w:g} mm is below the minimum feature width.", f"Use finger width >= {max(t, min_feature):.1f} mm.", "finger_w"))
    if sheet_width <= 0 or margin < 0 or gap < 0:
        messages.append(_msg("error", "LAYOUT_INVALID", "Sheet width must be positive, and margin/padding must be nonnegative.", "Increase sheet width and use nonnegative layout values.", "sheet_width"))
    if stroke <= 0:
        messages.append(_msg("error", "STROKE_INVALID", "SVG stroke width must be positive.", "Set stroke_mm > 0.", "stroke_mm"))

    return {
        "thickness": t,
        "kerf": kerf,
        "fit_clearance": clearance,
        "finger_w": finger_w,
        "min_fingers": min_fingers,
        "min_feature_width": min_feature,
        "min_web_mm": min_web,
        "max_row_width": sheet_width,
        "margin": margin,
        "gap": gap,
        "stroke_mm": stroke,
        "labels": _bool(params, "labels", default=True),
        "offset_kerf": _bool(params, "offset_kerf", default=False),
        "holding_tabs": _bool(params, "holding_tabs", default=False),
        "tab_width_mm": _num(params, "tab_width_mm", default=2.0),
        "finger_count_outer": None if params.get("finger_count_outer") in (None, "") else int(float(params["finger_count_outer"])),
        "finger_count_vertical": None if params.get("finger_count_vertical") in (None, "") else int(float(params["finger_count_vertical"])),
    }


def _box_dimensions(params: Dict[str, Any], common: Dict[str, Any], messages: List[WarningMsg]) -> Dict[str, float]:
    t = common["thickness"]
    dim_mode = str(params.get("dim_mode") or params.get("dimension_mode") or "internal")
    w = _num(params, "inner_w", "inner_width", default=135.0)
    d = _num(params, "inner_d", "inner_depth", default=90.0)
    h = _num(params, "inner_h", "inner_height", default=80.0)
    if dim_mode == "external":
        ext_w, ext_d, ext_h = w, d, h
        w = ext_w - 2 * t
        d = ext_d - 2 * t
        h = ext_h - t
        messages.append(_msg("info", "EXTERNAL_DIMENSIONS_CONVERTED", "External dimensions were converted to internal cavity dimensions.", "Review normalized_params for the derived internal dimensions.", "dim_mode"))
    return {"inner_w": w, "inner_d": d, "inner_h": h}


def _validate_box_domain(tid: str, norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    t = norm["thickness"]
    min_web = norm["min_web_mm"]
    min_feature = norm["min_feature_width"]
    min_inner_w = max(24.0, 4 * t + 2 * min_web)
    min_inner_d = max(24.0, 4 * t + 2 * min_web)
    min_inner_h = max(18.0, 3 * t + min_web)
    limits.update({"min_inner_w": min_inner_w, "min_inner_d": min_inner_d, "min_inner_h": min_inner_h})
    for field, min_value in (("inner_w", min_inner_w), ("inner_d", min_inner_d), ("inner_h", min_inner_h)):
        value = norm[field]
        if value < min_value:
            messages.append(
                _msg(
                    "error",
                    f"{field.upper()}_TOO_SMALL",
                    f"{field} {value:g} mm is too small for {t:g} mm material and {min_feature:g} mm minimum features.",
                    f"Increase {field} to at least {min_value:.1f} mm or reduce material thickness.",
                    field,
                )
            )

    outer_w = norm["inner_w"] + 2 * t
    outer_d = norm["inner_d"] + 2 * t
    wall_h = norm["inner_h"] + t
    limits.update({"outer_w": outer_w, "outer_d": outer_d, "wall_h": wall_h})
    target = norm["finger_w"] if norm["finger_w"] is not None else max(10.0, 3.0 * t)
    for edge_name, length in (("width", outer_w), ("depth", outer_d), ("height", wall_h)):
        count = compute_finger_count(length, target, min_fingers=norm["min_fingers"])
        pitch = length / max(1, count)
        if pitch < max(t, min_feature):
            messages.append(_msg("error", "FINGER_PITCH_TOO_SMALL", f"{edge_name} edge pitch {pitch:.2f} mm is below the minimum feature width.", "Increase dimensions or target finger width.", "finger_w"))

    largest_part = max(outer_w, outer_d, wall_h)
    if norm["max_row_width"] < largest_part + 2 * norm["margin"]:
        messages.append(_msg("error", "SHEET_WIDTH_TOO_SMALL", f"Sheet width {norm['max_row_width']:g} mm is smaller than the largest part plus margins.", f"Use sheet width >= {largest_part + 2 * norm['margin']:.1f} mm.", "sheet_width"))


def _validate_tray(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    t = norm["thickness"]
    front_h = norm["front_h"] if norm.get("front_h") is not None else max(t * 2.0, min(norm["inner_h"] * 0.45, 32.0))
    min_front = max(2 * t, norm["min_web_mm"] + t)
    limits["min_front_h"] = min_front
    if front_h < min_front:
        messages.append(_msg("error", "FRONT_HEIGHT_TOO_LOW", f"Front height {front_h:g} mm cannot support side/front joints.", f"Increase front_h to at least {min_front:.1f} mm.", "front_h"))
    if norm["scoop"]:
        max_depth = front_h - t
        if norm["scoop_depth"] >= max_depth:
            if norm.get("_scoop_depth_provided"):
                messages.append(_msg("error", "SCOOP_TOO_DEEP", "Scoop depth would erase most of the lowered front.", f"Use scoop_depth < {max_depth:.1f} mm.", "scoop_depth"))
            else:
                norm["scoop_depth"] = max(0.0, max_depth - 0.5)
                messages.append(_msg("info", "SCOOP_DEPTH_NORMALIZED", "Default scoop depth was reduced to preserve front material.", f"Using scoop_depth={norm['scoop_depth']:.1f} mm.", "scoop_depth"))
        if norm["scoop_r"] * 2 > limits["outer_w"] - 2 * norm["min_web_mm"]:
            messages.append(_msg("error", "SCOOP_TOO_WIDE", "Scoop radius collides with side material.", f"Use scoop_r <= {(limits['outer_w'] - 2 * norm['min_web_mm']) / 2:.1f} mm.", "scoop_r"))


def _validate_dispenser(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    t = norm["thickness"]
    margin = max(2 * t, norm["min_web_mm"])
    wall_h = limits["wall_h"]
    outer_w = limits["outer_w"]
    max_slot_w = outer_w - 2 * margin
    max_slot_h = wall_h - 2 * margin
    limits.update({"max_slot_width": max_slot_w, "max_slot_height": max_slot_h})
    if norm["slot_width"] <= 0 or norm["slot_width"] > max_slot_w:
        messages.append(_msg("error", "SLOT_WIDTH_INVALID", f"Slot width {norm['slot_width']:g} mm leaves insufficient side material.", f"Use slot_width between 1 and {max_slot_w:.1f} mm.", "slot_width"))
    if norm["slot_height"] <= 0 or norm["slot_height"] > max_slot_h:
        messages.append(_msg("error", "SLOT_HEIGHT_INVALID", f"Slot height {norm['slot_height']:g} mm leaves insufficient top/bottom material.", f"Use slot_height between 1 and {max_slot_h:.1f} mm.", "slot_height"))
    sy = wall_h - norm["slot_y_from_bottom"] - norm["slot_height"]
    if sy < margin or sy + norm["slot_height"] > wall_h - margin:
        messages.append(_msg("error", "SLOT_POSITION_INVALID", "Dispensing slot collides with front panel margins or joints.", f"Use slot_y_from_bottom so the slot stays between {margin:.1f} and {wall_h - margin:.1f} mm.", "slot_y_from_bottom"))


def _validate_window(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    margin = norm["window_margin"]
    required = max(norm["thickness"], norm["min_web_mm"])
    if margin < required:
        messages.append(_msg("error", "WINDOW_MARGIN_TOO_SMALL", f"Window margin {margin:g} mm is below required web {required:g} mm.", f"Use window_margin >= {required:.1f} mm.", "window_margin"))
    win_w = limits["outer_w"] - 2 * margin
    win_h = limits["wall_h"] - 2 * margin
    if win_w < norm["min_feature_width"] * 2 or win_h < norm["min_feature_width"] * 2:
        messages.append(_msg("error", "WINDOW_TOO_LARGE", "Window cutout leaves too little structural frame.", "Increase panel size or reduce window_margin.", "window_margin"))
    if norm["thumb_notch_depth"] + required > margin and win_h > 0:
        messages.append(_msg("warn", "THUMB_NOTCH_CLOSE_TO_WINDOW", "Thumb notch is close to the window frame.", "Reduce thumb_notch_depth or increase window_margin.", "thumb_notch_depth"))


def _validate_box_lid(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    if norm["lid_clearance"] < 0:
        messages.append(_msg("error", "LID_CLEARANCE_NEGATIVE", "Lid clearance cannot be negative.", "Use lid_clearance >= 0.", "lid_clearance"))
    if norm["lid_height"] < max(2 * norm["thickness"], norm["min_web_mm"]):
        messages.append(_msg("error", "LID_HEIGHT_TOO_LOW", "Lid wall height is too small for stable joints.", f"Use lid_height >= {max(2 * norm['thickness'], norm['min_web_mm']):.1f} mm.", "lid_height"))
    limits["lid_inner_w"] = limits["outer_w"] + 2 * norm["lid_clearance"]
    limits["lid_inner_d"] = limits["outer_d"] + 2 * norm["lid_clearance"]


def _validate_divider(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    count = norm["divider_count"]
    if count < 2:
        messages.append(_msg("error", "DIVIDER_COUNT_TOO_LOW", "Divider rack needs at least two bays.", "Set divider_count >= 2.", "divider_count"))
    bay_w = norm["inner_w"] / max(1, count)
    min_bay = max(3 * norm["thickness"], 2 * norm["min_web_mm"])
    limits["min_bay_width"] = min_bay
    if bay_w < min_bay:
        messages.append(_msg("error", "DIVIDER_BAYS_TOO_NARROW", f"Bay width {bay_w:.1f} mm is too narrow.", f"Use divider_count <= {max(2, int(norm['inner_w'] // min_bay))} or increase inner_w.", "divider_count"))


def _validate_card_shoe(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    for field in ("card_w", "card_h", "card_t"):
        if norm[field] <= 0:
            messages.append(_msg("error", f"{field.upper()}_INVALID", f"{field} must be positive.", f"Enter a measured {field}.", field))
    if norm["capacity"] <= 0:
        messages.append(_msg("error", "CAPACITY_INVALID", "Card capacity must be positive.", "Set capacity >= 1.", "capacity"))
    slot_h = norm["draw_slot_height"] if norm.get("draw_slot_height") is not None else max(1.0, min(3.0, norm["card_t"] + 0.6))
    limits["draw_slot_height"] = slot_h
    if slot_h < norm["card_t"] + 0.2:
        messages.append(_msg("error", "DRAW_SLOT_TOO_LOW", "Draw slot is too low for one card to exit.", f"Use draw_slot_height >= {norm['card_t'] + 0.2:.2f} mm.", "draw_slot_height"))
    if slot_h > norm["card_t"] + 2.5:
        messages.append(_msg("warn", "DRAW_SLOT_SPILL_RISK", "Draw slot may allow multiple cards to spill.", "Reduce draw_slot_height or add a hold-down lip.", "draw_slot_height"))
    if not 4 <= norm["ramp_angle_deg"] <= 22:
        messages.append(_msg("warn", "RAMP_ANGLE_OUTSIDE_TYPICAL", "Ramp angle is outside the typical 6-18 degree range.", "Prototype and adjust ramp angle.", "ramp_angle_deg"))


def _validate_candy(norm: Dict[str, Any], messages: List[WarningMsg], limits: Dict[str, Any]) -> None:
    if norm["max_piece"] <= 0:
        messages.append(_msg("error", "MAX_PIECE_INVALID", "max_piece must be positive.", "Measure the largest item and enter max_piece > 0.", "max_piece"))
    if norm["depth_layers_total"] < 2:
        messages.append(_msg("error", "DEPTH_LAYERS_TOO_FEW", "depth_layers_total must be at least 2.", "Use 8 for a typical 3mm educational prototype.", "depth_layers_total"))
    if norm["wheel_layers"] < 1 or norm["wheel_layers"] >= norm["depth_layers_total"]:
        messages.append(_msg("error", "WHEEL_LAYERS_INVALID", "wheel_layers must be >= 1 and less than depth_layers_total.", "Use wheel_layers=3 and depth_layers_total=8 to start.", "wheel_layers"))
    if norm["screw_d"] <= 0 or norm["axle_d"] <= 0:
        messages.append(_msg("error", "HOLE_DIAMETER_INVALID", "Screw and axle diameters must be positive.", "Enter positive screw_d and axle_d values.", "screw_d"))
    min_margin = norm["screw_d"] / 2 + norm["min_web_mm"]
    limits["min_screw_margin"] = min_margin
    if norm["screw_margin"] < min_margin:
        messages.append(_msg("error", "SCREW_MARGIN_TOO_SMALL", f"Screw margin {norm['screw_margin']:g} mm leaves too little material.", f"Use screw_margin >= {min_margin:.1f} mm.", "screw_margin"))

    p = max(1.0, norm["max_piece"])
    pocket_d = p + (2.5 if norm["irregular"] else 1.5)
    pocket_count = max(8, int(round(2 * math.pi * (pocket_d * 1.7) / max(10.0, pocket_d))))
    if pocket_count % 2:
        pocket_count += 1
    wheel_r = max(28.0, (pocket_count * pocket_d / (2 * math.pi)) * 1.30)
    pocket_ring_r = wheel_r - pocket_d * 0.85
    rim_web = wheel_r - (pocket_ring_r + pocket_d / 2)
    axle_clearance = pocket_ring_r - pocket_d / 2 - norm["axle_d"] / 2
    limits.update({"pocket_count": pocket_count, "wheel_r": wheel_r, "rim_web": rim_web, "axle_clearance": axle_clearance})
    if rim_web < norm["min_web_mm"]:
        messages.append(_msg("error", "POCKETS_TOO_CLOSE_TO_RIM", "Rotary wheel pockets leave too little rim material.", "Reduce max_piece or increase wheel scale.", "max_piece"))
    if axle_clearance < norm["min_web_mm"]:
        messages.append(_msg("error", "POCKETS_COLLIDE_WITH_AXLE", "Rotary wheel pockets are too close to the axle hole.", "Reduce max_piece or increase wheel scale.", "axle_d"))


def validate_template_params(template_id: str, params: Dict[str, Any]) -> ValidationResult:
    if not isinstance(params, dict):
        raise TypeError("params must be a dict")

    messages: List[WarningMsg] = []
    tid = _template(template_id, params, messages)
    common = _normalize_common(params, messages)
    norm: Dict[str, Any] = {"template_id": tid, **common}
    limits: Dict[str, Any] = {
        "kerf_full_width_mm": common["kerf"],
        "burn_radius_mm": KerfModel(common["kerf"]).burn_radius_mm,
    }
    max_odd_fit_imbalance = 0.54
    fit_imbalance = abs(2.0 * common["kerf"] - common["fit_clearance"])
    limits["max_odd_segment_fit_imbalance_mm"] = max_odd_fit_imbalance
    limits["odd_segment_fit_imbalance_mm"] = fit_imbalance
    if fit_imbalance > max_odd_fit_imbalance:
        messages.append(
            _msg(
                "error",
                "FIT_COMPENSATION_UNBALANCED",
                "This kerf/clearance combination cannot be compensated reliably with odd shared finger plans.",
                f"Use clearance closer to {2.0 * common['kerf']:.2f} mm, reduce kerf, or use nominal/no-kerf export after cutter calibration.",
                "fit_clearance",
            )
        )

    if tid == "calibration":
        norm["clearance_values"] = _clearance_values(params)
        if not norm["clearance_values"]:
            messages.append(_msg("error", "CALIBRATION_VALUES_EMPTY", "Calibration needs at least one clearance value.", "Provide clearance_values as a comma-separated list.", "clearance_values"))
    elif tid in {"tray_open_front", "dispenser_slot_front", "window_front", "box_with_lid", "divider_rack"}:
        norm.update(_box_dimensions(params, common, messages))
        norm.update(
            {
                "front_h": _maybe_num(params, "front_h", "front_height"),
                "scoop": _bool(params, "scoop", default=True),
                "scoop_r": _num(params, "scoop_r", "scoop_radius", default=22.0),
                "scoop_depth": _num(params, "scoop_depth", default=16.0),
                "_scoop_depth_provided": "scoop_depth" in params,
                "slot_width": _num(params, "slot_width", default=80.0),
                "slot_height": _num(params, "slot_height", default=18.0),
                "slot_y_from_bottom": _num(params, "slot_y_from_bottom", default=35.0),
                "window_margin": _num(params, "window_margin", default=12.0),
                "window_corner_r": _num(params, "window_corner_r", default=6.0),
                "thumb_notch_radius": _num(params, "thumb_notch_radius", default=10.0),
                "thumb_notch_depth": _num(params, "thumb_notch_depth", default=8.0),
                "lid": _bool(params, "lid", default=True),
                "lid_height": _num(params, "lid_height", default=25.0),
                "lid_clearance": _num(params, "lid_clearance", default=0.4),
                "divider_count": _int(params, "divider_count", "divider_bays", default=3),
            }
        )
        _validate_box_domain(tid, norm, messages, limits)
        if tid == "tray_open_front":
            _validate_tray(norm, messages, limits)
        elif tid == "dispenser_slot_front":
            _validate_dispenser(norm, messages, limits)
        elif tid == "window_front":
            _validate_window(norm, messages, limits)
        elif tid == "box_with_lid":
            _validate_box_lid(norm, messages, limits)
        elif tid == "divider_rack":
            _validate_divider(norm, messages, limits)
    elif tid == "card_shoe":
        norm.update(
            {
                "card_w": _num(params, "card_w", "card_width", default=63.0),
                "card_h": _num(params, "card_h", "card_height", default=88.0),
                "card_t": _num(params, "card_t", "card_thickness", default=0.35),
                "capacity": _int(params, "capacity", "capacity_cards", default=60),
                "ramp_angle_deg": _num(params, "ramp_angle_deg", default=12.0),
                "draw_slot_height": _maybe_num(params, "draw_slot_height"),
                "follower": _bool(params, "follower", "follower_enabled", default=False),
            }
        )
        _validate_card_shoe(norm, messages, limits)
    elif tid == "candy_machine_rotary_layered":
        norm.update(
            {
                "max_piece": _num(params, "max_piece", "max_piece_size", default=18.0),
                "irregular": _bool(params, "irregular", default=False),
                "hopper_h": _num(params, "hopper_h", "hopper_height", default=90.0),
                "depth_layers_total": _int(params, "depth_layers_total", default=8),
                "wheel_layers": _int(params, "wheel_layers", default=3),
                "screw_d": _num(params, "screw_d", "screw_diameter", default=3.2),
                "screw_margin": _num(params, "screw_margin", default=10.0),
                "axle_d": _num(params, "axle_d", "axle_diameter", default=6.0),
                "add_feet": _bool(params, "add_feet", default=False),
            }
        )
        _validate_candy(norm, messages, limits)

    target_final_tab_depth = common["thickness"]
    target_final_slot_depth = common["thickness"] + common["fit_clearance"]
    drawn_tab_depth = drawn_tab_depth_for_target(target_final_tab_depth, common["kerf"])
    drawn_slot_depth = drawn_slot_depth_for_target(target_final_slot_depth, common["kerf"])
    nominal = max(common["thickness"], common["min_feature_width"])
    drawn_tab_width = drawn_tab_width_for_target(nominal - common["fit_clearance"] / 2, common["kerf"])
    drawn_slot_width = drawn_slot_width_for_target(nominal + common["fit_clearance"] / 2, common["kerf"])
    limits["fit_model"] = {
        "target_final_tab_depth": target_final_tab_depth,
        "target_final_slot_depth": target_final_slot_depth,
        "drawn_tab_depth": drawn_tab_depth,
        "drawn_slot_depth": drawn_slot_depth,
        "expected_final_tab_depth": final_tab_depth_from_drawn(drawn_tab_depth, common["kerf"]),
        "expected_final_slot_depth": final_slot_depth_from_drawn(drawn_slot_depth, common["kerf"]),
        "sample_nominal_segment": nominal,
        "sample_drawn_tab_width": drawn_tab_width,
        "sample_drawn_slot_width": drawn_slot_width,
        "sample_final_tab_width": final_tab_width_from_drawn(drawn_tab_width, common["kerf"]),
        "sample_final_slot_width": final_slot_width_from_drawn(drawn_slot_width, common["kerf"]),
    }

    blocking = any(m.severity == "error" for m in messages)
    return ValidationResult(normalized_params=norm, messages=messages, blocking=blocking, computed_limits=limits)
