"""Rendering utilities for turning font glyphs into binary masks."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage import filters

__all__ = ["render_glyph_to_binary"]


def _load_font(font_path: str | Path, point_px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path), size=point_px)


def _glyph_bbox(font: ImageFont.FreeTypeFont, char: str) -> tuple[int, int, int, int]:
    bbox = font.getbbox(char, anchor="lt")
    if bbox is None:
        return (0, 0, 0, 0)
    return bbox


def _center_position(canvas_px: int, bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    x = (canvas_px - width) / 2.0 - left
    y = (canvas_px - height) / 2.0 - top
    return x, y


def _trim_margin(mask: np.ndarray, margin_px: int) -> np.ndarray:
    if not mask.any():
        return mask

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    y_indices = np.where(rows)[0]
    x_indices = np.where(cols)[0]
    y0 = max(int(y_indices[0]) - margin_px, 0)
    y1 = min(int(y_indices[-1]) + margin_px + 1, mask.shape[0])
    x0 = max(int(x_indices[0]) - margin_px, 0)
    x1 = min(int(x_indices[-1]) + margin_px + 1, mask.shape[1])
    return mask[y0:y1, x0:x1]


def render_glyph_to_binary(
    char: str,
    font_path: str | Path,
    point_px: int,
    canvas_px: int,
    margin_px: int,
    binarize: Literal["otsu", "fixed"] = "otsu",
    binary_threshold: int = 128,
) -> np.ndarray:
    """Render ``char`` into a binary numpy array using ``font_path``.

    The returned array is of dtype ``bool`` with ``True`` indicating the glyph
    foreground.
    """

    font = _load_font(font_path, point_px)
    image = Image.new("L", (canvas_px, canvas_px), 0)
    draw = ImageDraw.Draw(image)
    bbox = _glyph_bbox(font, char)
    x, y = _center_position(canvas_px, bbox)
    draw.text((x, y), char, fill=255, font=font)

    arr = np.array(image, dtype=np.uint8)
    if binarize == "otsu":
        threshold = filters.threshold_otsu(arr) if arr.any() else 0
    else:
        threshold = int(binary_threshold)
    mask = arr > threshold
    mask = _trim_margin(mask, margin_px)
    return mask.astype(bool)
