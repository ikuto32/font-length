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


def _compute_degree(skel: np.ndarray) -> np.ndarray:
    padded = np.pad(skel.astype(np.uint8), 1, mode="constant", constant_values=0)
    degree = np.zeros_like(skel, dtype=np.uint8)
    for dy, dx in _NEIGHBORS:
        degree += padded[1 + dy : 1 + dy + skel.shape[0], 1 + dx : 1 + dx + skel.shape[1]]
    return degree


def _prune_spurs(skel: np.ndarray, max_len: int) -> np.ndarray:
    if max_len <= 0:
        return skel

    work = skel.copy()
    changed = True
    while changed:
        changed = False
        degree = _compute_degree(work)
        endpoints = np.argwhere((work) & (degree == 1))
        to_clear: set[tuple[int, int]] = set()

        for y, x in endpoints:
            path: list[tuple[int, int]] = []
            current = (int(y), int(x))
            prev: tuple[int, int] | None = None
            steps = 0
            keep_path = True

            while True:
                path.append(current)
                cy, cx = current
                neighbors = []
                for dy, dx in _NEIGHBORS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < work.shape[0] and 0 <= nx < work.shape[1]:
                        if work[ny, nx] and (prev is None or (ny, nx) != prev):
                            neighbors.append((ny, nx))
                if not neighbors:
                    break

                next_pixel = neighbors[0]
                steps += 1
                prev = current
                current = next_pixel

                if steps > max_len:
                    keep_path = False
                    break

                deg = degree[current]
                if deg >= 3:
                    keep_path = False
                    break
                if deg <= 1:
                    break

            if keep_path and path:
                to_clear.update(path)

        if to_clear:
            for y, x in to_clear:
                work[y, x] = False
            changed = True

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
