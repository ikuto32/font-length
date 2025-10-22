"""Utility script for measuring the stroke length of specific characters."""
from __future__ import annotations

import argparse
from pathlib import Path

from font_length.config import Config
from font_length.measure import polylines_bounds, total_length
from font_length.morph import skeletonize_clean
from font_length.raster import render_glyph_to_binary
from font_length.svgout import polylines_to_svg_path_d, write_svg
from font_length.vectorize import skeleton_to_polylines


def measure_character(char: str, config: Config) -> dict[str, object]:
    if len(char) != 1:
        raise ValueError("Only single characters are supported")

    bw = render_glyph_to_binary(
        char,
        config.font_path,
        config.point_px,
        config.canvas_px,
        config.margin_px,
        binarize=config.binarize,
        binary_threshold=config.binary_threshold,
    )
    if bw.size == 0 or not bw.any():
        raise RuntimeError("Rendered glyph is empty")

    skeleton = skeletonize_clean(bw, config.min_obj_area, config.spur_prune_len)
    if skeleton.size == 0 or not skeleton.any():
        raise RuntimeError("Skeletonization produced no data")

    polylines = skeleton_to_polylines(skeleton)
    if not polylines:
        raise RuntimeError("Could not vectorize the skeleton")

    length = total_length(polylines)
    bounds = polylines_bounds(polylines)

    return {
        "char": char,
        "total_length": length,
        "bounds": bounds,
        "polylines": polylines,
        "path_d": polylines_to_svg_path_d(polylines, config.simplify_eps, scale=1.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the stroke length of a single character")
    parser.add_argument("char", help="Character to measure (single glyph)")
    parser.add_argument("font", help="Path to the font file (.otf/.ttf)")
    parser.add_argument("--out-svg", dest="out_svg", help="Optional path to write the generated SVG")
    parser.add_argument("--point-px", type=int, default=1800)
    parser.add_argument("--canvas-px", type=int, default=2200)
    parser.add_argument("--margin-px", type=int, default=128)
    parser.add_argument("--binarize", choices=["otsu", "fixed"], default="otsu")
    parser.add_argument("--binary-threshold", type=int, default=128)
    parser.add_argument("--min-obj-area", type=int, default=48)
    parser.add_argument("--spur-prune", type=int, default=8)
    parser.add_argument("--simplify-eps", type=float, default=2.0)
    parser.add_argument("--stroke-width", type=float, default=1.0)

    args = parser.parse_args()

    config = Config(
        font_path=args.font,
        out_dir="./out_svg",  # unused but required
        point_px=args.point_px,
        canvas_px=args.canvas_px,
        margin_px=args.margin_px,
        binarize=args.binarize,
        binary_threshold=args.binary_threshold,
        min_obj_area=args.min_obj_area,
        spur_prune_len=args.spur_prune,
        simplify_eps=args.simplify_eps,
        stroke_width=args.stroke_width,
    )

    result = measure_character(args.char, config)
    print(f"Character: {result['char']}")
    print(f"Total stroke length (px): {result['total_length']:.3f}")
    print(f"Bounds (min_x, min_y, width, height): {result['bounds']}")
    print(f"Polyline count: {len(result['polylines'])}")

    if args.out_svg:
        path = Path(args.out_svg)
        write_svg(
            result["path_d"],
            path,
            stroke_width=args.stroke_width,
            view_box=result["bounds"],
        )
        print(f"Wrote SVG to {path}")


if __name__ == "__main__":
    main()
