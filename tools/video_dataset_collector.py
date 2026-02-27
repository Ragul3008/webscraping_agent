"""
video_dataset_collector.py
──────────────────────────
Collects video dataset links. Uses broader filtering so more results pass through.
"""
from __future__ import annotations
from typing import List
from tools.search_tool import web_search, multi_search
from core.logger import get_logger
from core.models import VideoDatasetLink

log = get_logger(__name__)

_VIDEO_QUERY_TEMPLATES = [
    "{topic} video dataset download",
    "{topic} video dataset research",
    "{topic} dataset GitHub videos",
    "{topic} dataset Kaggle video",
    "{topic} video corpus download",
    "{topic} sign language recognition dataset",
]

_VIDEO_DOMAINS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "kaggle.com": "Kaggle",
    "github.com": "GitHub",
    "huggingface.co": "HuggingFace",
    "paperswithcode.com": "PapersWithCode",
    "zenodo.org": "Zenodo",
    "roboflow.com": "Roboflow",
    "ieee.org": "IEEE",
    "academia.edu": "Academia",
    "arxiv.org": "ArXiv",
    "drive.google.com": "GoogleDrive",
}

# Broad keywords — accept anything that could be a dataset resource
_INCLUDE_KEYWORDS = [
    "dataset", "data", "download", "corpus", "benchmark",
    "recognition", "classification", "annotation", "github",
    "kaggle", "huggingface", "video", "collection", "archive",
]

# Exclude pure tutorial/blog pages
_EXCLUDE_KEYWORDS = ["how to learn sign language", "buy now", "subscribe", "course enrollment"]


def _classify_source(url: str) -> str:
    for domain, label in _VIDEO_DOMAINS.items():
        if domain in url:
            return label
    return "Research"


def _is_relevant(title: str, snippet: str, url: str) -> bool:
    combined = (title + " " + snippet + " " + url).lower()
    # Must have at least one include keyword
    has_include = any(kw in combined for kw in _INCLUDE_KEYWORDS)
    # Must not be a pure tutorial/buy page
    has_exclude = any(kw in combined for kw in _EXCLUDE_KEYWORDS)
    return has_include and not has_exclude


async def collect_video_links(topic: str, max_links: int = 20) -> List[VideoDatasetLink]:
    queries = [t.format(topic=topic) for t in _VIDEO_QUERY_TEMPLATES]
    log.info(f"Video collector: searching with {len(queries)} queries for '{topic}'")

    results = await multi_search(queries, max_results_each=10)

    seen_urls: set = set()
    links: List[VideoDatasetLink] = []

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")

        if not url or url in seen_urls:
            continue

        if not _is_relevant(title, snippet, url):
            continue

        seen_urls.add(url)
        links.append(VideoDatasetLink(
            title=title,
            url=url,
            source=_classify_source(url),
            description=snippet[:300],
        ))

        if len(links) >= max_links:
            break

    # If still 0 results, add everything from search (no filter)
    if not links:
        log.info("  Video collector: relaxing filters — adding all search results")
        for r in results[:max_links]:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                links.append(VideoDatasetLink(
                    title=r.get("title", url),
                    url=url,
                    source=_classify_source(url),
                    description=r.get("snippet", "")[:300],
                ))

    log.info(f"Video collector: collected {len(links)} links for '{topic}'")
    return links