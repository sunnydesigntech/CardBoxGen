"""Fabrication and kerf/fit compensation models.

CardBoxGen treats ``kerf`` as the full width removed by the laser cut. The
centerline burn radius is therefore ``kerf / 2``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class KerfModel:
    """Full-width kerf model.

    ``kerf_full_width_mm`` is the whole slot burned by the laser. A cut line
    removes ``burn_radius_mm`` on each side of the centerline.
    """

    kerf_full_width_mm: float = 0.2

    @property
    def burn_radius_mm(self) -> float:
        return max(0.0, float(self.kerf_full_width_mm) / 2.0)


@dataclass(frozen=True)
class FitModel:
    kerf: KerfModel
    clearance_mm: float = 0.15
    thickness_mm: float = 3.0


def final_tab_width_from_drawn(drawn_width: float, kerf_full_width_mm: float) -> float:
    """External tab width after cutting."""

    return float(drawn_width) - float(kerf_full_width_mm)


def final_slot_width_from_drawn(drawn_width: float, kerf_full_width_mm: float) -> float:
    """Internal slot/gap width after cutting."""

    return float(drawn_width) + float(kerf_full_width_mm)


def drawn_tab_width_for_target(target_final_width: float, kerf_full_width_mm: float) -> float:
    return float(target_final_width) + float(kerf_full_width_mm)


def drawn_slot_width_for_target(target_final_width: float, kerf_full_width_mm: float) -> float:
    return float(target_final_width) - float(kerf_full_width_mm)


def final_tab_depth_from_drawn(drawn_depth: float, kerf_full_width_mm: float, *, open_edge: bool = True) -> float:
    """Final external finger/tab depth under the open-edge outline model."""

    return float(drawn_depth) - (float(kerf_full_width_mm) if open_edge else KerfModel(kerf_full_width_mm).burn_radius_mm)


def final_slot_depth_from_drawn(drawn_depth: float, kerf_full_width_mm: float, *, open_edge: bool = True) -> float:
    """Final open-edge recess/slot depth.

    For finger joints, the recess is open to a cut edge. CardBoxGen uses a
    conservative open-edge model where the surrounding edge and the recess
    bottom both move by one burn radius, so final depth grows by the full kerf.
    """

    return float(drawn_depth) + (float(kerf_full_width_mm) if open_edge else KerfModel(kerf_full_width_mm).burn_radius_mm)


def drawn_tab_depth_for_target(target_final_depth: float, kerf_full_width_mm: float, *, open_edge: bool = True) -> float:
    return float(target_final_depth) + (float(kerf_full_width_mm) if open_edge else KerfModel(kerf_full_width_mm).burn_radius_mm)


def drawn_slot_depth_for_target(target_final_depth: float, kerf_full_width_mm: float, *, open_edge: bool = True) -> float:
    return float(target_final_depth) - (float(kerf_full_width_mm) if open_edge else KerfModel(kerf_full_width_mm).burn_radius_mm)


def compensated_segment_widths(
    nominal_widths: Sequence[float],
    tabs_mask: Sequence[bool],
    *,
    kerf_full_width_mm: float,
    clearance_mm: float,
    total_length: float,
) -> List[float]:
    """Draw tab/slot segment widths for a target clearance and exact edge length.

    The target final tab width is nominal minus half the requested clearance.
    The target final slot width is nominal plus half the requested clearance.
    Drawn widths are then normalized to preserve the edge's exact total length.
    """

    if len(nominal_widths) != len(tabs_mask):
        raise ValueError("width and mask lengths differ")
    if not nominal_widths:
        return []

    c = float(clearance_mm)
    k = float(kerf_full_width_mm)
    raw: List[float] = []
    for nominal, is_tab in zip(nominal_widths, tabs_mask):
        nominal = float(nominal)
        if is_tab:
            target_final = nominal - c / 2.0
            drawn = drawn_tab_width_for_target(target_final, k)
        else:
            target_final = nominal + c / 2.0
            drawn = drawn_slot_width_for_target(target_final, k)
        raw.append(max(0.1, drawn))

    scale = float(total_length) / max(1e-9, sum(raw))
    out = [w * scale for w in raw]
    out[-1] += float(total_length) - sum(out)
    return out


def final_segment_widths(drawn_widths: Sequence[float], tabs_mask: Sequence[bool], *, kerf_full_width_mm: float) -> List[float]:
    if len(drawn_widths) != len(tabs_mask):
        raise ValueError("width and mask lengths differ")
    out: List[float] = []
    for drawn, is_tab in zip(drawn_widths, tabs_mask):
        if is_tab:
            out.append(final_tab_width_from_drawn(drawn, kerf_full_width_mm))
        else:
            out.append(final_slot_width_from_drawn(drawn, kerf_full_width_mm))
    return out
