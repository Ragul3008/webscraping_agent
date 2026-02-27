"""
github_scraper.py
─────────────────
Searches GitHub for repositories that contain datasets matching a query.
Uses the GitHub Search API (no auth = 10 req/min; set GITHUB_TOKEN for 30 req/min).
"""

from __future__ import annotations

import asyncio
import os
from typing import List

import aiohttp

from core.config import config
from core.logger import get_logger
from core.models import DatasetEntry, DataSource, DownloadStatus

log = get_logger(__name__)

_API = "https://api.github.com/search/repositories"
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Optional personal access token from env
_GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
if _GH_TOKEN:
    _HEADERS["Authorization"] = f"Bearer {_GH_TOKEN}"


async def search_github_datasets(query: str, limit: int = 10) -> List[DatasetEntry]:
    """
    Search GitHub repositories for datasets.
    Appends 'dataset' to the query to improve relevance.
    """
    full_query = f"{query} dataset"
    params = {
        "q": full_query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit, 30),
    }
    entries: List[DatasetEntry] = []

    for attempt in range(config.agent.retry_attempts):
        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(
                    _API,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=config.agent.request_timeout),
                ) as resp:
                    if resp.status == 403:
                        log.warning("GitHub rate limit hit — add GITHUB_TOKEN to .env")
                        return entries
                    resp.raise_for_status()
                    data = await resp.json()

            for item in data.get("items", [])[:limit]:
                # Only include repos that look like datasets
                topics: List[str] = item.get("topics", [])
                desc: str = (item.get("description") or "").lower()
                name: str = item.get("full_name", "")

                is_dataset = (
                    "dataset" in topics
                    or "dataset" in name.lower()
                    or "dataset" in desc
                    or "data" in topics
                )

                entries.append(
                    DatasetEntry(
                        name=item.get("full_name", ""),
                        description=item.get("description") or "",
                        source=DataSource.GITHUB,
                        download_url=item.get("html_url", ""),
                        data_type=_infer_type(topics, desc),
                        download_status=DownloadStatus.LINK_ONLY,
                        tags=topics,
                        extra={
                            "stars": item.get("stargazers_count", 0),
                            "language": item.get("language", ""),
                            "clone_url": item.get("clone_url", ""),
                            "is_dataset_repo": is_dataset,
                        },
                    )
                )
            break  # Success — exit retry loop

        except Exception as exc:
            wait = config.agent.retry_backoff ** attempt
            log.warning(f"GitHub search attempt {attempt+1} failed: {exc}. Retry in {wait:.1f}s")
            await asyncio.sleep(wait)

    log.info(f"GitHub: found {len(entries)} repos for '{full_query}'")
    return entries


def _infer_type(topics: List[str], desc: str) -> str:
    combined = " ".join(topics) + " " + desc
    if "image" in combined or "vision" in combined or "photo" in combined:
        return "image"
    if "video" in combined:
        return "video"
    if "audio" in combined or "speech" in combined:
        return "audio"
    if "nlp" in combined or "text" in combined or "nlp" in combined:
        return "text"
    return "tabular"
