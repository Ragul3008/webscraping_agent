"""
image_downloader.py
───────────────────
Downloads images from Google (via icrawler) or Bing as a fallback.
Images are saved inside downloads/images/<sanitised_query>/.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List

from core.config import config
from core.logger import get_logger
from core.models import ImageEntry

log = get_logger(__name__)


def _sanitise(text: str) -> str:
    """Convert a query string into a safe directory name."""
    return re.sub(r"[^\w\-]", "_", text.strip().lower())[:60]


def _download_images_sync(query: str, max_num: int, dest_dir: Path) -> List[ImageEntry]:
    """
    Synchronous image download using icrawler.
    Tries Google first, falls back to Bing.
    """
    entries: List[ImageEntry] = []
    dest_dir.mkdir(parents=True, exist_ok=True)

    crawlers_to_try = []
    try:
        from icrawler.builtin import GoogleImageCrawler, BingImageCrawler  # type: ignore

        crawlers_to_try = [
            ("Google", GoogleImageCrawler),
            ("Bing", BingImageCrawler),
        ]
    except ImportError:
        log.error("icrawler not installed — pip install icrawler")
        return entries

    for engine_name, CrawlerClass in crawlers_to_try:
        try:
            log.info(f"  📸 {engine_name}: downloading up to {max_num} images for '{query}'")
            crawler = CrawlerClass(
                storage={"root_dir": str(dest_dir)},
                log_level="ERROR",         # Suppress icrawler's noisy logs
            )
            crawler.crawl(
                keyword=query,
                max_num=max_num,
                file_idx_offset=0,
            )

            # Collect saved files
            image_files = list(dest_dir.iterdir())
            for img_file in image_files:
                if img_file.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                    entries.append(
                        ImageEntry(
                            filename=img_file.name,
                            local_path=str(img_file),
                            query=query,
                        )
                    )

            if entries:
                log.info(f"  ✓  {engine_name}: {len(entries)} images saved to {dest_dir}")
                return entries  # Success — no need to try next engine

        except Exception as exc:
            log.warning(f"  {engine_name} crawler failed: {exc}")

    return entries


async def download_images(query: str, max_num: int | None = None) -> List[ImageEntry]:
    """
    Async wrapper around the synchronous icrawler download.
    Returns a list of ImageEntry objects for all downloaded files.
    """
    count = max_num or config.agent.max_images
    safe_query = _sanitise(query)
    dest_dir = config.storage.images_dir / safe_query

    loop = asyncio.get_event_loop()
    entries = await loop.run_in_executor(
        None, _download_images_sync, query, count, dest_dir
    )

    if not entries:
        log.warning(f"  No images downloaded for '{query}'")

    return entries
