"""Finger-joint planning and kerf/clearance compensation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .geometry import Point, add, dot, is_axis_aligned_dir, mul


class EdgeFamily:
    OUTER = "outer"
    VERTICAL = "vertical"
    LID = "lid"


@dataclass(frozen=True)
class EdgeKey:
    panel: str
    edge: str


@dataclass
class FingerPlan:
    """Shared source of truth for one mating edge pair."""

    length: float
    count: int
    widths: List[float]
    start_with_tab_on_a: bool = True

    def tabs_mask_for_a(self) -> List[bool]:
        return [((i % 2 == 0) if self.start_with_tab_on_a else (i % 2 == 1)) for i in range(self.count)]

    def tabs_mask(self, *, invert: bool = False) -> List[bool]:
        mask = self.tabs_mask_for_a()
        return [not v for v in mask] if invert else mask

    def complement_mask(self) -> List[bool]:
        return [not v for v in self.tabs_mask_for_a()]

    def drawn_widths_for_side(self, *, kerf_mm: float, clearance_mm: float, invert: bool = False) -> List[float]:
        return compensate_segment_widths(
            self.widths,
            self.tabs_mask(invert=invert),
            kerf_mm=kerf_mm,
            clearance_mm=clearance_mm,
            total_length=self.length,
        )


def compute_finger_count(
    length: float,
    target_finger_w: float,
    *,
    min_fingers: int = 3,
    force_odd: bool = True,
    explicit: Optional[int] = None,
) -> int:
    """Select a deterministic finger count from edge length."""

    if length <= 0:
        return 0
    if explicit is not None:
        n = int(explicit)
        if n < 1:
            raise ValueError("explicit finger count must be >= 1")
    else:
        denom = max(1e-6, float(target_finger_w))
        n = int(math.floor(float(length) / denom))
        n = max(int(min_fingers), n)
    if force_odd and n % 2 == 0:
        n += 1
    return n


def joint_depths_drawn(*, thickness: float, kerf_mm: float, clearance_mm: float) -> Tuple[float, float]:
    """Return drawn tab depth and drawn slot depth.

    Slot rule: final_slot ~= drawn_slot + kerf. Target final slot is
    material thickness + clearance, therefore drawn_slot = thickness +
    clearance - kerf.
    """

    t = max(0.0, float(thickness))
    k = float(kerf_mm)
    c = float(clearance_mm)
    return t, max(0.0, t + c - k)


def compensate_segment_widths(
    nominal_widths: List[float],
    tabs_mask: List[bool],
    *,
    kerf_mm: float,
    clearance_mm: float,
    total_length: float,
) -> List[float]:
    """Apply explicit kerf/clearance width compensation and normalize length."""

    if len(nominal_widths) != len(tabs_mask):
        raise ValueError("width and mask lengths differ")
    if not nominal_widths:
        return []
    k = float(kerf_mm)
    c = float(clearance_mm)
    tab_delta = k - c / 2.0
    slot_delta = c / 2.0 - k
    raw = [max(0.1, float(w) + (tab_delta if is_tab else slot_delta)) for w, is_tab in zip(nominal_widths, tabs_mask)]
    scale = float(total_length) / max(1e-9, sum(raw))
    out = [w * scale for w in raw]
    out[-1] += float(total_length) - sum(out)
    return out


def build_finger_plan(
    length: float,
    *,
    count: int,
    kerf_mm: float = 0.0,
    clearance_mm: float = 0.0,
    start_with_tab_on_a: bool = True,
) -> FingerPlan:
    if count <= 0:
        raise ValueError("finger count must be positive")
    pitch = float(length) / int(count)
    widths = [pitch] * int(count)
    widths[-1] += float(length) - sum(widths)
    return FingerPlan(length=float(length), count=int(count), widths=widths, start_with_tab_on_a=start_with_tab_on_a)


def finger_edge_points(
    start: Point,
    dirv: Point,
    normal_out: Point,
    plan: FingerPlan,
    *,
    thickness: float,
    kerf_mm: float,
    clearance_mm: float,
    invert_tabs: bool,
) -> List[Point]:
    """Generate a Manhattan polyline along an edge using a shared FingerPlan."""

    if plan.length <= 0:
        return []
    if not is_axis_aligned_dir(dirv) or not is_axis_aligned_dir(normal_out):
        raise ValueError("dirv/normal must be axis-aligned")
    if abs(dot(dirv, normal_out)) > 1e-9:
        raise ValueError("dirv and normal must be perpendicular")

    tab_depth, slot_depth = joint_depths_drawn(thickness=thickness, kerf_mm=kerf_mm, clearance_mm=clearance_mm)
    mask = plan.tabs_mask(invert=invert_tabs)
    widths = plan.drawn_widths_for_side(kerf_mm=kerf_mm, clearance_mm=clearance_mm, invert=invert_tabs)

    pts: List[Point] = []
    p = start
    for w, is_tab in zip(widths, mask):
        depth = tab_depth if is_tab else slot_depth
        off = mul(normal_out, depth if is_tab else -depth)
        p_out = add(p, off)
        p2 = add(p, mul(dirv, w))
        p2_out = add(p2, off)
        pts.append(p_out)
        pts.append(p2_out)
        pts.append(p2)
        p = p2
    return pts
