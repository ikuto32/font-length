"""SVG path helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .vectorize import rdp

__all__ = ["polylines_to_svg_path_d", "write_svg"]


def polylines_to_svg_path_d(
    polylines: Iterable[Iterable[tuple[float, float]]],
    simplify_eps: float = 2.0,
    scale: float = 1.0,
) -> str:
    """Convert polylines to a SVG path string."""

    commands: list[str] = []
    for polyline in polylines:
        pts = list(polyline)
        if len(pts) < 2:
            continue
        if simplify_eps > 0:
            pts = rdp(pts, simplify_eps)
        if len(pts) < 2:
            continue
        move = pts[0]
        segments = [
            f"L {pt[0] * scale:.3f} {pt[1] * scale:.3f}" for pt in pts[1:]
        ]
        command = " ".join([f"M {move[0] * scale:.3f} {move[1] * scale:.3f}"] + segments)
        commands.append(command)
    return " ".join(commands)


def write_svg(
    path_d: str,
    out_path: str | Path,
    stroke_width: float = 1.0,
    view_box: tuple[float, float, float, float] | None = None,
) -> None:
    """Write ``path_d`` to an SVG file at ``out_path``."""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not path_d:
        width = height = 0
        min_x = min_y = 0
    elif view_box is not None:
        min_x, min_y, width, height = view_box
    else:
        min_x = min_y = 0.0
        width = height = 0.0

    view_box_str = f"{min_x:.3f} {min_y:.3f} {max(width, 1.0):.3f} {max(height, 1.0):.3f}"

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" stroke=\"black\" stroke-width=\"{stroke_width}\" viewBox=\"{view_box_str}\">\n  <path d=\"{path_d}\"/>\n</svg>\n"""
    out_path.write_text(svg, encoding="utf-8")
