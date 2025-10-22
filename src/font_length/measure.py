"""Utilities for measuring polyline lengths and bounds."""
from __future__ import annotations

from typing import Iterable, Sequence, Tuple

__all__ = ["polyline_total_length", "total_length", "polylines_bounds"]


Point = Tuple[float, float]


def polyline_total_length(polyline: Sequence[Point]) -> float:
    if len(polyline) < 2:
        return 0.0
    total = 0.0
    for (x0, y0), (x1, y1) in zip(polyline, polyline[1:]):
        dx = x1 - x0
        dy = y1 - y0
        total += (dx * dx + dy * dy) ** 0.5
    return total


def total_length(polylines: Iterable[Sequence[Point]]) -> float:
    return sum(polyline_total_length(poly) for poly in polylines)


def polylines_bounds(polylines: Iterable[Sequence[Point]]) -> tuple[float, float, float, float]:
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    has_point = False
    for poly in polylines:
        for x, y in poly:
            has_point = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not has_point:
        return (0.0, 0.0, 0.0, 0.0)
    return (min_x, min_y, max_x - min_x, max_y - min_y)
