"""Morphological helpers for skeleton extraction."""
from __future__ import annotations

import numpy as np
from skimage.morphology import remove_small_objects, skeletonize

__all__ = ["skeletonize_clean"]

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


def _is_valid_neighbor(skel: np.ndarray, y: int, x: int, ny: int, nx: int) -> bool:
    if not (0 <= ny < skel.shape[0] and 0 <= nx < skel.shape[1]):
        return False
    if not skel[ny, nx]:
        return False
    dy = ny - y
    dx = nx - x
    if abs(dy) == 1 and abs(dx) == 1:
        if skel[y, nx] or skel[ny, x]:
            return False
    return True


def _compute_degree(skel: np.ndarray) -> np.ndarray:
    degree = np.zeros_like(skel, dtype=np.uint8)
    coords = np.argwhere(skel)
    for y, x in coords:
        count = 0
        for dy, dx in _NEIGHBORS:
            ny, nx = int(y + dy), int(x + dx)
            if _is_valid_neighbor(skel, int(y), int(x), ny, nx):
                count += 1
        degree[int(y), int(x)] = count
    return degree


def _prune_spurs(skel: np.ndarray, max_len: int) -> np.ndarray:
    if max_len <= 0:
        return skel

    work = skel.copy()
    degree = _compute_degree(work)
    endpoints = np.argwhere((work) & (degree == 1))
    to_clear: set[tuple[int, int]] = set()

    for y, x in endpoints:
        path: list[tuple[int, int]] = []
        current = (int(y), int(x))
        prev: tuple[int, int] | None = None
        steps = 0
        branch_detected = False

        while steps < max_len:
            path.append(current)
            cy, cx = current
            neighbors = []
            for dy, dx in _NEIGHBORS:
                ny, nx = cy + dy, cx + dx
                if not _is_valid_neighbor(work, cy, cx, ny, nx):
                    continue
                if prev is not None and (ny, nx) == prev:
                    continue
                neighbors.append((ny, nx))

            if not neighbors:
                break

            next_pixel = neighbors[0]
            dy = next_pixel[0] - cy
            dx = next_pixel[1] - cx

            next_neighbors = []
            for dy2, dx2 in _NEIGHBORS:
                ny2, nx2 = next_pixel[0] + dy2, next_pixel[1] + dx2
                if not _is_valid_neighbor(work, next_pixel[0], next_pixel[1], ny2, nx2):
                    continue
                if (ny2, nx2) == (cy, cx):
                    continue
                next_neighbors.append((ny2, nx2))

            if degree[next_pixel] >= 3:
                branch_detected = True
            else:
                for ny2, nx2 in next_neighbors:
                    dy2 = ny2 - next_pixel[0]
                    dx2 = nx2 - next_pixel[1]
                    if (dy2, dx2) != (dy, dx):
                        branch_detected = True
                        break

            prev = current
            current = next_pixel
            steps += 1

            if not next_neighbors:
                break

        if branch_detected and path:
            to_clear.update(path)

    if to_clear:
        for y, x in to_clear:
            work[y, x] = False

    return work


def skeletonize_clean(bw: np.ndarray, min_obj_area: int, spur_prune_len: int) -> np.ndarray:
    """Perform skeletonization after simple morphological cleanup."""

    if bw.dtype != bool:
        bw = bw.astype(bool)

    cleaned = remove_small_objects(bw, min_size=max(min_obj_area, 1))
    skel = skeletonize(cleaned)
    if not skel.any():
        return skel
    return _prune_spurs(skel, spur_prune_len)
