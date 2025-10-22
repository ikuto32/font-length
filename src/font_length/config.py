"""Configuration objects and helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__all__ = ["Config", "load_config_file"]


class Config(BaseModel):
    font_path: str
    out_dir: str = Field(default="./out_svg")

    point_px: int = Field(default=1800, ge=1)
    canvas_px: int = Field(default=2200, ge=1)
    margin_px: int = Field(default=128, ge=0)

    binarize: Literal["otsu", "fixed"] = "otsu"
    binary_threshold: int = Field(default=128, ge=0, le=255)

    min_obj_area: int = Field(default=48, ge=0)
    spur_prune_len: int = Field(default=8, ge=0)

    simplify_eps: float = Field(default=2.0, ge=0.0)

    workers: int | Literal["auto"] = "auto"

    joyo_url: str = Field(
        default="https://raw.githubusercontent.com/NHV33/joyo-kanji-compilation/master/kanji_string.txt"
    )
    joyo_cache: str = Field(default=".cache/joyo_kanji.txt")

    log_level: str = Field(default="INFO")
    stroke_width: float = Field(default=1.0, gt=0.0)

    class Config:
        validate_assignment = True

    @field_validator("workers", mode="before")
    @classmethod
    def _validate_workers(cls, value: Any) -> int | Literal["auto"]:
        if value == "auto" or value is None:
            return "auto"
        if isinstance(value, str):
            if value.lower() == "auto":
                return "auto"
            value = int(value)
        if isinstance(value, int) and value <= 0:
            raise ValueError("workers must be positive or 'auto'")
        return value

    def resolved_workers(self) -> int:
        if self.workers == "auto":
            import multiprocessing

            return max(1, min(8, multiprocessing.cpu_count()))
        return int(self.workers)

    def model_dump_config(self) -> dict[str, Any]:
        data = self.model_dump()
        return data


def load_config_file(path: str | Path) -> Config:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Configuration file must describe a mapping")
    return Config(**data)
