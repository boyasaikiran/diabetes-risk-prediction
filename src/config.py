"""Centralised configuration loading."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging once. Never log health values."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@lru_cache(maxsize=1)
def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load YAML config, applying environment overrides."""
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if os.environ.get("DRP_MODEL_DIR"):
        cfg["paths"]["model_dir"] = os.environ["DRP_MODEL_DIR"]
    return cfg


def resolve(rel: str) -> Path:
    """Resolve a config path against the project root (absolute paths kept)."""
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p
