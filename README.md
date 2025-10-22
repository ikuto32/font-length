# font-length

Utilities for converting OpenType fonts into single-line SVG approximations and
computing total stroke lengths across the Joyo kanji set.  The package renders
glyphs into high-resolution bitmaps, skeletonizes them, vectorises the resulting
center lines, and writes individual SVG files alongside a length report.

## Installation

```bash
pip install -e .
```

This project depends on Pillow, scikit-image, numpy, requests, pydantic, PyYAML,
and tqdm.

## Command line interface

```bash
joyo2svg \
  --font /path/to/font.otf \
  --out-dir ./out_svg \
  --point-px 1800 \
  --canvas-px 2200 \
  --margin-px 128 \
  --binarize otsu \
  --min-obj-area 48 \
  --spur-prune 8 \
  --simplify-eps 2.0 \
  --workers auto
```

The converter downloads the Joyo kanji list on first run and caches it under
`.cache/joyo_kanji.txt`.  Each glyph is rendered to `out_svg/UXXXX.svg` where the
suffix is the Unicode codepoint.  A CSV report (`stroke_length_report.csv`) and
`summary.json` are produced in the same directory.

## Library usage

```python
from font_length import Config, convert_font_to_singleline_svgs

summary = convert_font_to_singleline_svgs(
    Config(font_path="/path/to/font.otf", out_dir="./out_svg")
)
print(summary.top_lengths[:5])
```

The resulting :class:`Summary` object also serializes to JSON via
``summary.to_dict()`` for downstream processing.
