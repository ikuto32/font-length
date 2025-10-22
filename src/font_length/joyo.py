"""Utilities for loading the Joyo kanji character set.

This module downloads the canonical list of Joyo kanji characters from
``NHV33/joyo-kanji-compilation`` and caches the result locally.  The cache is
optional but recommended so that repeated executions do not hit the network.
"""
from __future__ import annotations

from pathlib import Path

import requests

__all__ = ["get_joyo_chars"]


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as fh:
        return fh.read()


def get_joyo_chars(url: str, cache: str | None = None) -> list[str]:
    """Return the list of Joyo kanji characters.

    Parameters
    ----------
    url:
        Remote URL that provides the kanji list.  The referenced file is
        expected to contain a single line string of characters (the format used
        by ``joyo-kanji-compilation``).
    cache:
        Optional path to a local cache file.  When provided the function will
        try to read the cache before performing the HTTP request.  After a
        successful download the content is written back to the cache path.
    """

    cache_path = Path(cache) if cache else None
    if cache_path and cache_path.exists():
        return list(_read_text(cache_path).strip())

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text.strip()

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")

    return list(text)
