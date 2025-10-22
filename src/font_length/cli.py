"""Command line interface for the converter."""
from __future__ import annotations

import argparse
import logging
from typing import Any

from .config import Config, load_config_file
from .runner import convert_font_to_singleline_svgs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert fonts to single-line SVGs for the Joyo kanji set")
    parser.add_argument("--config", help="Optional YAML/JSON configuration file")
    parser.add_argument("--font", dest="font_path", help="Path to the font file (.otf/.ttf)")
    parser.add_argument("--out-dir", dest="out_dir", help="Output directory for generated assets")
    parser.add_argument("--point-px", type=int, dest="point_px", help="Font rendering size in pixels")
    parser.add_argument("--canvas-px", type=int, dest="canvas_px", help="Canvas size in pixels")
    parser.add_argument("--margin-px", type=int, dest="margin_px", help="Margin to preserve around glyphs")
    parser.add_argument("--binarize", choices=["otsu", "fixed"], help="Binarization strategy")
    parser.add_argument(
        "--binary-threshold", type=int, dest="binary_threshold", help="Threshold for fixed binarization"
    )
    parser.add_argument("--min-obj-area", type=int, dest="min_obj_area", help="Minimum object area to retain")
    parser.add_argument("--spur-prune", type=int, dest="spur_prune_len", help="Spur pruning length in pixels")
    parser.add_argument("--simplify-eps", type=float, dest="simplify_eps", help="RDP simplification epsilon")
    parser.add_argument("--workers", help="Number of worker processes or 'auto'")
    parser.add_argument("--joyo-url", dest="joyo_url", help="URL pointing to the kanji list")
    parser.add_argument("--joyo-cache", dest="joyo_cache", help="Path to the cached kanji list")
    parser.add_argument("--log-level", dest="log_level", help="Logging level (DEBUG/INFO/WARN/ERROR)")
    parser.add_argument("--stroke-width", dest="stroke_width", type=float, help="SVG stroke width")
    return parser


def _merge_config(cli_args: argparse.Namespace, base: Config | None) -> Config:
    data: dict[str, Any]
    if base is None:
        data = {}
    else:
        data = base.model_dump()

    for field in Config.model_fields:
        if field == "font_path" and not getattr(cli_args, field, None):
            continue
        value = getattr(cli_args, field, None)
        if value is not None:
            data[field] = value

    if "font_path" not in data or not data["font_path"]:
        raise SystemExit("--font must be provided via CLI or configuration file")

    return Config(**data)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    base_config = None
    if args.config:
        base_config = load_config_file(args.config)

    config = _merge_config(args, base_config)

    summary = convert_font_to_singleline_svgs(config)
    logging.getLogger(__name__).info(
        "Finished conversion: processed=%d failures=%d", summary.processed, len(summary.failures)
    )


if __name__ == "__main__":  # pragma: no cover
    main()
