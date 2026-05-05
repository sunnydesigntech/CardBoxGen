"""JSON-safe public generation API used by CLI and Pyodide."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .models import BoxParams, GenerationResult, WarningMsg
from .panels import Panel
from .presets import (
    build_box_with_lid,
    build_calibration,
    build_candy_machine_rotary_layered,
    build_card_shoe,
    build_dispenser_slot_front,
    build_divider_rack,
    build_tray_open_front,
    build_window_front,
)
from .svg import make_svg
from .version import __version__

Builder = Callable[..., Tuple[List[Panel], List[WarningMsg], dict]]

TEMPLATE_BUILDERS: Dict[str, Builder] = {
    "tray_open_front": build_tray_open_front,
    "dispenser_slot_front": build_dispenser_slot_front,
    "window_front": build_window_front,
    "box_with_lid": build_box_with_lid,
    "divider_rack": build_divider_rack,
    "card_shoe": build_card_shoe,
    "candy_machine_rotary_layered": build_candy_machine_rotary_layered,
    "calibration": build_calibration,
}

ALIASES: Dict[str, str] = {
    "card_shoe_front_draw": "card_shoe",
    "candy_rotary_wheel": "candy_machine_rotary_layered",
    "rotary_wheel": "candy_machine_rotary_layered",
}


def normalize_template_id(template_id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[str, List[WarningMsg]]:
    tid = str(template_id or "").strip()
    warnings: List[WarningMsg] = []
    if not tid and params:
        tid = str(params.get("preset") or params.get("template_id") or "").strip()
    if not tid:
        tid = "tray_open_front"
        warnings.append(WarningMsg("warn", "TEMPLATE_DEFAULTED", "No template_id was provided; using tray_open_front.", "Pass template_id explicitly."))
    if tid in ALIASES:
        new_tid = ALIASES[tid]
        warnings.append(WarningMsg("warn", "TEMPLATE_ALIAS", f"Template '{tid}' is deprecated; generated '{new_tid}' instead.", f"Use template_id '{new_tid}'."))
        tid = new_tid
    return tid, warnings


def _num(params: Dict[str, Any], *keys: str, default: float) -> float:
    for key in keys:
        if key in params and params[key] is not None and params[key] != "":
            return float(params[key])
    return float(default)


def _int(params: Dict[str, Any], *keys: str, default: int) -> int:
    for key in keys:
        if key in params and params[key] is not None and params[key] != "":
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


def _clearance_values(params: Dict[str, Any]) -> Optional[List[float]]:
    raw = params.get("clearance_values")
    if raw is None:
        return None
    if isinstance(raw, str):
        return [float(x.strip()) for x in raw.split(",") if x.strip()]
    if isinstance(raw, Iterable):
        return [float(x) for x in raw]
    return None


def _builder_kwargs(template_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    common = {
        "thickness": _num(params, "thickness", default=3.0),
        "kerf": _num(params, "kerf", "kerf_mm", default=0.2),
        "fit_clearance": _num(params, "fit_clearance", "clearance", "clearance_mm", default=0.15),
        "finger_w": _maybe_num(params, "finger_w", "finger_width"),
        "min_fingers": _int(params, "min_fingers", default=3),
        "labels": _bool(params, "labels", default=True),
        "finger_count_outer": params.get("finger_count_outer"),
        "finger_count_vertical": params.get("finger_count_vertical"),
    }
    if common["finger_count_outer"] in ("", None):
        common["finger_count_outer"] = None
    else:
        common["finger_count_outer"] = int(common["finger_count_outer"])
    if common["finger_count_vertical"] in ("", None):
        common["finger_count_vertical"] = None
    else:
        common["finger_count_vertical"] = int(common["finger_count_vertical"])

    if template_id == "calibration":
        return {
            "thickness": common["thickness"],
            "kerf": common["kerf"],
            "clearance_values": _clearance_values(params),
            "labels": common["labels"],
        }

    common_box = {
        "inner_w": _num(params, "inner_w", "inner_width", default=135.0),
        "inner_d": _num(params, "inner_d", "inner_depth", default=90.0),
        "inner_h": _num(params, "inner_h", "inner_height", default=80.0),
        **common,
    }

    if template_id == "tray_open_front":
        return {
            **common_box,
            "front_h": _maybe_num(params, "front_h", "front_height"),
            "scoop": _bool(params, "scoop", default=True),
            "scoop_r": _num(params, "scoop_r", "scoop_radius", default=22.0),
            "scoop_depth": _num(params, "scoop_depth", default=16.0),
        }
    if template_id == "dispenser_slot_front":
        return {
            **common_box,
            "slot_width": _num(params, "slot_width", default=80.0),
            "slot_height": _num(params, "slot_height", default=18.0),
            "slot_y_from_bottom": _num(params, "slot_y_from_bottom", default=35.0),
            "thumb_notch_radius": _num(params, "thumb_notch_radius", default=10.0),
            "thumb_notch_depth": _num(params, "thumb_notch_depth", default=8.0),
        }
    if template_id == "window_front":
        return {
            **common_box,
            "window_margin": _num(params, "window_margin", default=12.0),
            "window_corner_r": _num(params, "window_corner_r", default=6.0),
            "thumb_notch_radius": _num(params, "thumb_notch_radius", default=10.0),
            "thumb_notch_depth": _num(params, "thumb_notch_depth", default=8.0),
        }
    if template_id == "box_with_lid":
        return {
            **common_box,
            "lid": _bool(params, "lid", default=True),
            "lid_height": _num(params, "lid_height", default=25.0),
            "lid_clearance": _num(params, "lid_clearance", default=0.4),
            "thumb_notch_radius": _num(params, "thumb_notch_radius", default=10.0),
            "thumb_notch_depth": _num(params, "thumb_notch_depth", default=8.0),
        }
    if template_id == "divider_rack":
        return {
            **common_box,
            "divider_count": _int(params, "divider_count", "divider_bays", default=3),
        }
    if template_id == "card_shoe":
        return {
            **common,
            "card_w": _num(params, "card_w", "card_width", default=63.0),
            "card_h": _num(params, "card_h", "card_height", default=88.0),
            "card_t": _num(params, "card_t", "card_thickness", default=0.35),
            "capacity": _int(params, "capacity", "capacity_cards", default=60),
            "ramp_angle_deg": _num(params, "ramp_angle_deg", default=12.0),
            "draw_slot_height": _maybe_num(params, "draw_slot_height"),
            "follower": _bool(params, "follower", "follower_enabled", default=False),
        }
    if template_id == "candy_machine_rotary_layered":
        return {
            **common,
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
    return common_box


def build_design(template_id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[List[Panel], List[WarningMsg], Dict[str, Any]]:
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise TypeError("params must be a dict")
    tid, alias_warnings = normalize_template_id(template_id, params)
    if tid not in TEMPLATE_BUILDERS:
        valid = ", ".join(sorted(TEMPLATE_BUILDERS))
        raise ValueError(f"Unknown template_id: {tid}. Valid templates: {valid}")
    kwargs = _builder_kwargs(tid, params)
    panels, warnings, meta = TEMPLATE_BUILDERS[tid](**kwargs)
    all_warnings = alias_warnings + list(warnings)
    meta = dict(meta)
    meta["template_id"] = tid
    meta["cardboxgen_version"] = __version__
    meta["warnings"] = [w.to_dict() for w in all_warnings]
    return panels, all_warnings, meta


def build_bundle_files(template_id: str, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, str]:
    summary = (
        f"# CardBoxGen Project Summary\n\n"
        f"- Version: {__version__}\n"
        f"- Template: {template_id}\n"
        f"- Material thickness: {params.get('thickness', 3.0)} mm\n"
        f"- Kerf: {params.get('kerf', params.get('kerf_mm', 0.2))} mm\n"
        f"- Clearance: {params.get('fit_clearance', params.get('clearance_mm', 0.15))} mm\n"
    )
    assembly = (
        "# Assembly Guide\n\n"
        "1. Cut the SVG using the CUT layer.\n"
        "2. Dry fit panels before applying glue.\n"
        "3. Sand lightly only if the calibration strip indicates the fit is too tight.\n"
    )
    bom = (
        "# Bill of Materials\n\n"
        "- Laser-cut sheet material matching the configured thickness\n"
        "- Wood glue or acrylic cement as appropriate\n"
        "- Optional screws/axle hardware for mechanism templates\n"
    )
    metadata = json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True)
    params_json = json.dumps(params, ensure_ascii=False, indent=2, sort_keys=True)
    return {
        "project_summary.md": summary,
        "assembly_guide.md": assembly,
        "bom.md": bom,
        "metadata.json": metadata,
        "params.json": params_json,
    }


def generate_svg(template_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise TypeError("params must be a dict")
    panels, warnings, meta = build_design(template_id, params)
    tid = str(meta.get("template_id", template_id))
    svg = make_svg(
        panels,
        meta=meta,
        sheet_width=_num(params, "max_row_width", "sheet_width", default=340.0),
        labels=_bool(params, "labels", default=True),
        offset_kerf=_bool(params, "offset_kerf", default=False),
        kerf_mm=_num(params, "kerf", "kerf_mm", default=0.2),
        layout_margin_mm=_num(params, "margin", "layout_margin_mm", default=10.0),
        layout_padding_mm=_num(params, "gap", "layout_padding_mm", default=12.0),
        stroke_mm=_num(params, "stroke_mm", default=0.2),
        holding_tabs=_bool(params, "holding_tabs", default=False),
        tab_width_mm=_num(params, "tab_width_mm", default=2.0),
    )
    return GenerationResult(svg=svg, warnings=warnings, meta=meta, bundle_files=build_bundle_files(tid, params, meta)).to_dict()


def build_panels_for_preset(params: BoxParams) -> List[Panel]:
    panels, _, _ = build_design(params.preset, params.to_api_params())
    return panels


def generate_svg_with_warnings(params: BoxParams) -> Tuple[str, List[str]]:
    result = generate_svg(params.preset, params.to_api_params())
    return result["svg"], [w["message"] for w in result["warnings"]]


def build_calibration_svg(
    *,
    thickness: float,
    kerf_mm: float,
    clearance_values: Iterable[float],
    out_path: str,
    **kwargs,
) -> None:
    result = generate_svg(
        "calibration",
        {
            "thickness": thickness,
            "kerf": kerf_mm,
            "clearance_values": list(clearance_values),
            "labels": kwargs.get("labels", True),
        },
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result["svg"])
