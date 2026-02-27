"""
uci_scraper.py
──────────────
Searches and optionally downloads datasets from the UCI Machine
Learning Repository (https://archive.ics.uci.edu).
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from core.config import config
from core.logger import get_logger
from core.models import DatasetEntry, DataSource, DownloadStatus

log = get_logger(__name__)

_BASE = "https://archive.ics.uci.edu"
_SEARCH_URL = f"{_BASE}/datasets?search={{query}}&skip=0&take=10&sort=desc&orderBy=NumHits"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
    for attempt in range(config.agent.retry_attempts):
        try:
            async with session.get(
                url,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=config.agent.request_timeout),
            ) as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as exc:
            wait = config.agent.retry_backoff ** attempt
            log.debug(f"  UCI fetch attempt {attempt+1} failed ({exc}) — retry in {wait:.1f}s")
            await asyncio.sleep(wait)
    return ""


async def search_uci(query: str, limit: int = 10) -> List[DatasetEntry]:
    """Search UCI repository and return dataset metadata."""
    search_url = _SEARCH_URL.format(query=query.replace(" ", "+"))
    entries: List[DatasetEntry] = []

    async with aiohttp.ClientSession() as session:
        html = await _fetch(session, search_url)
        if not html:
            log.warning("UCI: empty response from search")
            return entries

        soup = BeautifulSoup(html, "html.parser")

        # UCI uses React; data may be in <script> or standard HTML depending on version
        # Try scraping dataset cards
        cards = soup.select("li[class*='DatasetCard']") or soup.select("div[class*='dataset']")

        if not cards:
            # Fallback: find all links pointing to /dataset/
            links = soup.find_all("a", href=re.compile(r"/dataset/\d+"))
            seen: set = set()
            for link in links[:limit]:
                href = link.get("href", "")
                if href in seen:
                    continue
                seen.add(href)
                full_url = urljoin(_BASE, href)
                name = link.get_text(strip=True) or href.split("/")[-1]
                entries.append(
                    DatasetEntry(
                        name=name,
                        description="",
                        source=DataSource.UCI,
                        download_url=full_url,
                        data_type="tabular",
                        download_status=DownloadStatus.PENDING,
                    )
                )
        else:
            for card in cards[:limit]:
                title_el = card.select_one("[class*='title'], h2, h3, strong")
                name = title_el.get_text(strip=True) if title_el else "Unknown"
                link_el = card.find("a", href=True)
                href = link_el["href"] if link_el else ""
                full_url = urljoin(_BASE, href) if href else ""
                desc_el = card.select_one("[class*='description'], p")
                desc = desc_el.get_text(strip=True) if desc_el else ""
                entries.append(
                    DatasetEntry(
                        name=name,
                        description=desc,
                        source=DataSource.UCI,
                        download_url=full_url,
                        data_type="tabular",
                        download_status=DownloadStatus.PENDING,
                    )
                )

        # Enrich entries: visit each dataset page to find direct download link
        for entry in entries:
            if entry.download_url:
                await _enrich_entry(session, entry)

    log.info(f"UCI: found {len(entries)} datasets for '{query}'")
    return entries


async def _enrich_entry(session: aiohttp.ClientSession, entry: DatasetEntry) -> None:
    """Visit the dataset page and look for a direct file download link."""
    html = await _fetch(session, entry.download_url)
    if not html:
        entry.download_status = DownloadStatus.MANUAL_REQUIRED
        return

    soup = BeautifulSoup(html, "html.parser")

    # Look for description
    if not entry.description:
        desc_el = soup.select_one(".dataset-abstract, [class*='abstract'], [class*='description']")
        if desc_el:
            entry.description = desc_el.get_text(strip=True)[:500]

    # Look for download button / link
    dl_link = soup.find("a", href=re.compile(r"\.(zip|csv|data|arff|xlsx?|tar\.gz)$", re.I))
    if dl_link:
        entry.extra["direct_download"] = urljoin(_BASE, dl_link["href"])
        entry.download_status = DownloadStatus.PENDING
    else:
        entry.download_status = DownloadStatus.MANUAL_REQUIRED


async def download_uci_dataset(entry: DatasetEntry) -> str:
    """Attempt to download a UCI dataset file directly."""
    direct_url = entry.extra.get("direct_download", "")
    if not direct_url:
        log.info(f"  UCI: no direct download link for '{entry.name}'")
        return ""

    dest_dir = config.storage.datasets_dir / "uci"
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = direct_url.split("/")[-1] or f"{entry.name}.zip"
    dest_file = dest_dir / filename

    log.info(f"  ⬇  Downloading UCI: {direct_url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                direct_url,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                resp.raise_for_status()
                data = await resp.read()
                dest_file.write_bytes(data)
        log.info(f"  ✓  UCI saved to {dest_file}")
        return str(dest_file)
    except Exception as exc:
        log.warning(f"  UCI download failed: {exc}")
        return ""
