"""
search_tool.py
──────────────
Web search — supports ddgs (new) and duckduckgo_search (old), plus SerpAPI.
"""
from __future__ import annotations
import asyncio
from typing import Dict, List
import aiohttp
from core.config import config
from core.logger import get_logger

log = get_logger(__name__)


def _ddg_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Try ddgs first (new package name), fall back to duckduckgo_search (old)."""
    results: List[Dict[str, str]] = []

    # Try new package name: ddgs
    try:
        from ddgs import DDGS  # type: ignore
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except ImportError:
        pass
    except Exception as exc:
        log.debug(f"ddgs search failed: {exc}")

    # Fall back to old package name: duckduckgo_search
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from duckduckgo_search import DDGS  # type: ignore
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except ImportError:
        pass
    except Exception as exc:
        log.debug(f"duckduckgo_search fallback failed: {exc}")

    log.warning(f"All search backends failed for: {query!r}. Run: pip install ddgs")
    return results


async def _serpapi_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    key = config.serpapi_key
    params = {"q": query, "api_key": key, "num": max_results, "engine": "google"}
    results: List[Dict[str, str]] = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://serpapi.com/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                data = await resp.json()
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
    except Exception as exc:
        log.warning(f"SerpAPI failed: {exc}")
    return results


async def web_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    log.info(f"🔍 Searching: {query!r}")
    if config.serpapi_key:
        results = await _serpapi_search(query, max_results)
        if results:
            return results
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _ddg_search, query, max_results)
    log.debug(f"  Search returned {len(results)} results")
    return results


async def multi_search(queries: List[str], max_results_each: int = 8) -> List[Dict[str, str]]:
    tasks = [web_search(q, max_results_each) for q in queries]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    seen_urls: set = set()
    combined: List[Dict[str, str]] = []
    for batch in raw:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                combined.append(item)
    log.info(f"  Multi-search: {len(combined)} unique results")
    return combined