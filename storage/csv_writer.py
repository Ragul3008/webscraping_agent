"""
csv_writer.py
─────────────
Exports datasets, images, and video links to separate CSV files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.config import config
from core.logger import get_logger
from core.models import AgentResult

log = get_logger(__name__)


def _stem(query: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in query)[:40]


def save_csv(result: AgentResult) -> dict[str, Path]:
    """Save datasets, images, and video links to CSV. Returns paths."""
    base = config.storage.results_dir
    base.mkdir(parents=True, exist_ok=True)
    stem = _stem(result.query)
    paths: dict[str, Path] = {}

    # Datasets CSV
    if result.datasets:
        df = pd.DataFrame([d.model_dump() for d in result.datasets])
        p = base / f"{stem}_datasets.csv"
        df.to_csv(p, index=False, encoding="utf-8")
        log.info(f"  📊 Datasets CSV → {p}")
        paths["datasets"] = p

    # Images CSV
    if result.images_downloaded:
        df = pd.DataFrame([i.model_dump() for i in result.images_downloaded])
        p = base / f"{stem}_images.csv"
        df.to_csv(p, index=False, encoding="utf-8")
        log.info(f"  📊 Images CSV → {p}")
        paths["images"] = p

    # Video links CSV
    if result.video_dataset_links:
        df = pd.DataFrame([v.model_dump() for v in result.video_dataset_links])
        p = base / f"{stem}_video_links.csv"
        df.to_csv(p, index=False, encoding="utf-8")
        log.info(f"  📊 Video links CSV → {p}")
        paths["video_links"] = p

    return paths
