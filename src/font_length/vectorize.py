"""Vectorisation helpers for skeleton arrays."""
from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np

__all__ = ["skeleton_to_polylines", "rdp"]

_NEIGHBORS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]

Point = Tuple[float, float]
Pixel = Tuple[int, int]


def _iter_neighbors(shape: tuple[int, int], pixel: Pixel) -> Iterable[Pixel]:
    y, x = pixel
    h, w = shape
    for dy, dx in _NEIGHBORS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w:
            yield ny, nx


def _edge(a: Pixel, b: Pixel) -> tuple[Pixel, Pixel]:
    return (a, b) if a <= b else (b, a)


def _pixel_to_point(pixel: Pixel) -> Point:
    y, x = pixel
    return float(x), float(y)


def skeleton_to_polylines(skel: np.ndarray) -> list[list[Point]]:
    """Convert a skeleton bitmap into polylines."""

    if skel.size == 0:
        return []

    coordinates = [tuple(pt) for pt in np.argwhere(skel)]
    if not coordinates:
        return []

    coord_set = set(coordinates)
    degree = {
        pixel: sum((neighbor in coord_set) for neighbor in _iter_neighbors(skel.shape, pixel))
        for pixel in coordinates
    }

    polylines: list[list[Point]] = []
    visited_edges: set[tuple[Pixel, Pixel]] = set()

    def trace_path(start: Pixel, first_neighbor: Pixel) -> None:
        edge = _edge(start, first_neighbor)
        if edge in visited_edges:
            return
        visited_edges.add(edge)

        path: list[Pixel] = [start, first_neighbor]
        prev = start
        current = first_neighbor

        while True:
            deg = degree.get(current, 0)
            neighbors = [n for n in _iter_neighbors(skel.shape, current) if n in coord_set and n != prev]
            if not neighbors:
                break
            if deg != 2:
                break
            nxt = neighbors[0]
            edge = _edge(current, nxt)
            if edge in visited_edges:
                break
            visited_edges.add(edge)
            if nxt == start:
                path.append(nxt)
                break
            path.append(nxt)
            prev, current = current, nxt

        if len(path) >= 2:
            polylines.append([_pixel_to_point(p) for p in path])

    for pixel in coordinates:
        if degree.get(pixel, 0) != 2:
            for neighbor in _iter_neighbors(skel.shape, pixel):
                if neighbor in coord_set:
                    trace_path(pixel, neighbor)

    for pixel in coordinates:
        for neighbor in _iter_neighbors(skel.shape, pixel):
            if neighbor in coord_set:
                trace_path(pixel, neighbor)

    return polylines


def _perpendicular_distance(point: Point, start: Point, end: Point) -> float:
    if start == end:
        return float(np.hypot(point[0] - start[0], point[1] - start[1]))

    x0, y0 = point
    x1, y1 = start
    x2, y2 = end

    num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    den = float(np.hypot(x2 - x1, y2 - y1))
    return num / den


def rdp(points: Sequence[Point], epsilon: float) -> list[Point]:
    """Ramer–Douglas–Peucker simplification."""

    if len(points) < 2 or epsilon <= 0:
        return list(points)

    start = points[0]
    end = points[-1]
    max_dist = 0.0
    index = -1

    for i in range(1, len(points) - 1):
        dist = _perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            index = i

    if max_dist > epsilon and index != -1:
        left = rdp(points[: index + 1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right

    return [start, end]
