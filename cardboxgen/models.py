"""Typed public models and validation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WarningMsg:
    severity: str
    code: str
    message: str
    fix: str = ""
    field: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        data = {
            "severity": str(self.severity),
            "code": str(self.code),
            "message": str(self.message),
            "fix": str(self.fix),
        }
        if self.field:
            data["field"] = str(self.field)
        return data


@dataclass
class ValidationResult:
    normalized_params: Dict[str, Any] = field(default_factory=dict)
    messages: List[WarningMsg] = field(default_factory=list)
    blocking: bool = False
    computed_limits: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "normalized_params": self.normalized_params,
            "messages": [m.to_dict() for m in self.messages],
            "blocking": self.blocking,
            "computed_limits": self.computed_limits,
        }


@dataclass
class BoxParams:
    """Back-compatible box/tray parameters used by the CLI and legacy wrapper."""

    variant: str = "A"
    preset: str = "tray_open_front"

    inner_width: float = 70.0
    inner_depth: float = 95.0
    inner_height: float = 120.0
    thickness: float = 3.0

    kerf_mm: float = 0.20
    clearance_mm: float = 0.15

    finger_width: Optional[float] = None
    min_fingers: int = 3
    finger_count_outer: Optional[int] = None
    finger_count_vertical: Optional[int] = None

    lid: bool = True
    lid_height: float = 25.0
    lid_clearance: float = 0.4

    front_height: Optional[float] = None
    scoop: bool = False
    scoop_radius: float = 22.0
    scoop_depth: float = 18.0

    slot_width: float = 80.0
    slot_height: float = 18.0
    slot_y_from_bottom: float = 35.0

    divider_bays: int = 3

    card_width: float = 63.0
    card_height: float = 88.0
    card_thickness: float = 0.35
    capacity_cards: int = 60
    side_clearance: float = 1.0
    top_clearance: float = 2.0
    back_clearance: float = 2.0
    ramp_angle_deg: float = 12.0
    draw_slot_height: Optional[float] = None
    follower_enabled: bool = False

    max_piece_size: float = 18.0
    irregular: bool = False
    axle_diameter: float = 6.0
    hopper_height: float = 90.0
    depth_layers_total: int = 8
    wheel_layers: int = 3
    screw_diameter: float = 3.2
    screw_margin: float = 10.0
    add_feet: bool = False

    window_margin: float = 18.0
    window_corner_r: float = 6.0
    thumb_notch_radius: float = 10.0
    thumb_notch_depth: float = 8.0

    labels: bool = True
    sheet_width: float = 320.0
    layout_margin_mm: float = 10.0
    layout_padding_mm: float = 12.0
    stroke_mm: float = 0.2
    export: str = "single_svg"
    offset_kerf: bool = False
    holding_tabs: bool = False
    tab_width_mm: float = 2.0

    def to_api_params(self) -> Dict[str, Any]:
        return {
            "inner_w": self.inner_width,
            "inner_d": self.inner_depth,
            "inner_h": self.inner_height,
            "thickness": self.thickness,
            "kerf": self.kerf_mm,
            "fit_clearance": self.clearance_mm,
            "finger_w": self.finger_width,
            "min_fingers": self.min_fingers,
            "finger_count_outer": self.finger_count_outer,
            "finger_count_vertical": self.finger_count_vertical,
            "front_h": self.front_height,
            "scoop": self.scoop,
            "scoop_r": self.scoop_radius,
            "scoop_depth": self.scoop_depth,
            "slot_width": self.slot_width,
            "slot_height": self.slot_height,
            "slot_y_from_bottom": self.slot_y_from_bottom,
            "divider_count": self.divider_bays,
            "card_w": self.card_width,
            "card_h": self.card_height,
            "card_t": self.card_thickness,
            "capacity": self.capacity_cards,
            "ramp_angle_deg": self.ramp_angle_deg,
            "draw_slot_height": self.draw_slot_height,
            "follower": self.follower_enabled,
            "max_piece": self.max_piece_size,
            "irregular": self.irregular,
            "axle_d": self.axle_diameter,
            "hopper_h": self.hopper_height,
            "depth_layers_total": self.depth_layers_total,
            "wheel_layers": self.wheel_layers,
            "screw_d": self.screw_diameter,
            "screw_margin": self.screw_margin,
            "add_feet": self.add_feet,
            "window_margin": self.window_margin,
            "window_corner_r": self.window_corner_r,
            "thumb_notch_radius": self.thumb_notch_radius,
            "thumb_notch_depth": self.thumb_notch_depth,
            "max_row_width": self.sheet_width,
            "margin": self.layout_margin_mm,
            "gap": self.layout_padding_mm,
            "stroke_mm": self.stroke_mm,
            "labels": self.labels,
            "offset_kerf": self.offset_kerf,
            "holding_tabs": self.holding_tabs,
            "tab_width_mm": self.tab_width_mm,
            "lid": self.lid,
            "lid_height": self.lid_height,
            "lid_clearance": self.lid_clearance,
        }


@dataclass
class GenerationResult:
    svg: str
    warnings: List[WarningMsg] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    bundle_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "svg": self.svg,
            "warnings": [w.to_dict() for w in self.warnings],
            "meta": self.meta,
            "bundle_files": self.bundle_files,
        }


def dataclass_dict(obj: Any) -> Dict[str, Any]:
    return asdict(obj)
