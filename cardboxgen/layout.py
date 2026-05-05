"""Simple deterministic sheet layout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .geometry import BBox, bbox_intersects
from .panels import Panel


@dataclass
class PlacedPanel:
    panel: Panel
    x: float
    y: float
    bbox: BBox


def arrange_panels(
    panels: List[Panel],
    *,
    sheet_width: float = 320.0,
    margin: float = 10.0,
    gap: float = 12.0,
) -> Tuple[List[PlacedPanel], float, float]:
    placed: List[PlacedPanel] = []
    x = float(margin)
    y = float(margin)
    row_h = 0.0
    total_w = float(margin)
    total_h = float(margin)
    usable_width = max(float(sheet_width), 2 * float(margin) + 1.0)

    for panel in panels:
        x0, y0, x1, y1 = panel.bbox()
        bw = x1 - x0
        bh = y1 - y0
        if placed and x + bw > usable_width - margin:
            x = float(margin)
            y += row_h + float(gap)
            row_h = 0.0
        gx = x - x0
        gy = y - y0
        panel_bbox = (x, y, x + bw, y + bh)
        placed.append(PlacedPanel(panel=panel, x=gx, y=gy, bbox=panel_bbox))
        x += bw + float(gap)
        row_h = max(row_h, bh)
        total_w = max(total_w, x)
        total_h = max(total_h, y + row_h)

    return placed, total_w + float(margin), total_h + float(margin)


def has_overlaps(placed: List[PlacedPanel]) -> bool:
    for i, a in enumerate(placed):
        for b in placed[i + 1 :]:
            if bbox_intersects(a.bbox, b.bbox):
                return True
    return False
