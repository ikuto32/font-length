"""High level orchestration utilities."""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from tqdm import tqdm

from .config import Config
from .joyo import get_joyo_chars
from .measure import polylines_bounds, total_length
from .morph import skeletonize_clean
from .raster import render_glyph_to_binary
from .svgout import polylines_to_svg_path_d, write_svg
from .vectorize import skeleton_to_polylines

__all__ = ["convert_font_to_singleline_svgs", "Summary"]


@dataclass
class GlyphResult:
    char: str
    codepoint: int
    path_d: str
    svg_filename: str
    total_length: float
    bounds: tuple[float, float, float, float]
    polyline_count: int
    skeleton_pixels: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class GlyphFailure:
    char: str
    codepoint: int
    reason: str
    message: str | None = None


@dataclass
class Summary:
    processed: int
    failures: list[GlyphFailure]
    duration_seconds: float
    top_lengths: list[tuple[str, float, str]]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "processed": self.processed,
            "failures": [f.__dict__ for f in self.failures],
            "duration_seconds": self.duration_seconds,
            "top_lengths": [
                {"char": char, "total_length": length, "svg": svg} for char, length, svg in self.top_lengths
            ],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class _WorkerConfig:
    font_path: str
    point_px: int
    canvas_px: int
    margin_px: int
    binarize: str
    binary_threshold: int
    min_obj_area: int
    spur_prune_len: int
    simplify_eps: float


def _compute_metrics(polylines: list[list[tuple[float, float]]]) -> dict[str, Any]:
    if not polylines:
        return {"polyline_count": 0, "mean_segment_len": 0.0}
    total = total_length(polylines)
    count = len(polylines)
    return {"polyline_count": count, "mean_segment_len": total / max(count, 1)}


def _process_char(char: str, cfg: _WorkerConfig) -> tuple[str, dict[str, Any] | None, GlyphFailure | None]:
    codepoint = ord(char)
    try:
        bw = render_glyph_to_binary(
            char,
            cfg.font_path,
            cfg.point_px,
            cfg.canvas_px,
            cfg.margin_px,
            binarize=cfg.binarize,
            binary_threshold=cfg.binary_threshold,
        )
        if bw.size == 0 or not bw.any():
            return char, None, GlyphFailure(char, codepoint, "empty")

        skel = skeletonize_clean(bw, cfg.min_obj_area, cfg.spur_prune_len)
        if skel.size == 0 or not skel.any():
            return char, None, GlyphFailure(char, codepoint, "noskeleton")

        skeleton_pixels = int(np.count_nonzero(skel))
        polylines = skeleton_to_polylines(skel)
        if not polylines:
            return char, None, GlyphFailure(char, codepoint, "nopolyline")

        length = total_length(polylines)
        bounds = polylines_bounds(polylines)
        path_d = polylines_to_svg_path_d(polylines, cfg.simplify_eps, scale=1.0)
        metrics = _compute_metrics(polylines)
        metrics.update(
            {
                "char": char,
                "codepoint": codepoint,
                "path_d": path_d,
                "bounds": bounds,
                "total_length": length,
                "skeleton_pixels": skeleton_pixels,
            }
        )
        return char, metrics, None
    except Exception as exc:  # pragma: no cover - defensive
        return char, None, GlyphFailure(char, codepoint, "error", message=str(exc))


def _iter_process_chars(chars: Iterable[str], cfg: _WorkerConfig, workers: int):
    if workers == 1:
        for ch in chars:
            yield _process_char(ch, cfg)
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_process_char, ch, cfg): ch for ch in chars}
            for future in as_completed(futures):
                yield future.result()


def convert_font_to_singleline_svgs(cfg: Config) -> Summary:
    """Execute the end-to-end conversion returning a :class:`Summary`."""

    logging.basicConfig(level=getattr(logging, cfg.log_level.upper(), logging.INFO))
    logger = logging.getLogger(__name__)

    start_ts = datetime.utcnow()
    chars = get_joyo_chars(cfg.joyo_url, cfg.joyo_cache)
    logger.info("Loaded %d characters", len(chars))

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "stroke_length_report.csv"
    results: list[GlyphResult] = []
    failures: list[GlyphFailure] = []

    worker_cfg = _WorkerConfig(
        font_path=cfg.font_path,
        point_px=cfg.point_px,
        canvas_px=cfg.canvas_px,
        margin_px=cfg.margin_px,
        binarize=cfg.binarize,
        binary_threshold=cfg.binary_threshold,
        min_obj_area=cfg.min_obj_area,
        spur_prune_len=cfg.spur_prune_len,
        simplify_eps=cfg.simplify_eps,
    )

    workers = cfg.resolved_workers()
    logger.info("Using %d worker(s)", workers)

    progress = tqdm(total=len(chars), desc="Processing", unit="char")

    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["char", "codepoint_hex", "total_length_px", "svg_file", "polyline_count", "skeleton_pixels"])

        for _, metrics, failure in _iter_process_chars(chars, worker_cfg, workers):
            progress.update(1)
            if failure:
                failures.append(failure)
                logger.warning("Skipping %s (%s)", failure.char, failure.reason)
                continue
            assert metrics is not None
            svg_filename = f"U{metrics['codepoint']:04X}.svg"
            path = out_dir / svg_filename
            bounds = metrics["bounds"]
            write_svg(
                metrics["path_d"],
                path,
                stroke_width=cfg.stroke_width,
                view_box=bounds,
            )
            writer.writerow(
                [
                    metrics["char"],
                    f"{metrics['codepoint']:04X}",
                    f"{metrics['total_length']:.3f}",
                    svg_filename,
                    metrics.get("polyline_count", 0),
                    metrics.get("skeleton_pixels", 0),
                ]
            )
            results.append(
                GlyphResult(
                    char=metrics["char"],
                    codepoint=metrics["codepoint"],
                    path_d=metrics["path_d"],
                    svg_filename=svg_filename,
                    total_length=metrics["total_length"],
                    bounds=bounds,
                    polyline_count=metrics.get("polyline_count", 0),
                    skeleton_pixels=metrics.get("skeleton_pixels", 0),
                )
            )

    progress.close()

    duration = (datetime.utcnow() - start_ts).total_seconds()
    results.sort(key=lambda r: r.total_length, reverse=True)
    top_lengths = [(res.char, res.total_length, res.svg_filename) for res in results[:20]]

    summary = Summary(
        processed=len(results),
        failures=failures,
        duration_seconds=duration,
        top_lengths=top_lengths,
        metadata={
            "font_path": cfg.font_path,
            "point_px": cfg.point_px,
            "canvas_px": cfg.canvas_px,
            "margin_px": cfg.margin_px,
            "simplify_eps": cfg.simplify_eps,
            "workers": workers,
            "total_characters": len(chars),
            "failures": len(failures),
        },
    )

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Processed %d glyphs (failures=%d) in %.2fs", len(results), len(failures), duration)
    if top_lengths:
        logger.info("Top character by stroke length: %s %.3f", top_lengths[0][0], top_lengths[0][1])

    return summary
