"""
kaggle_tool.py — fixed for all Kaggle package versions
"""
from __future__ import annotations
import asyncio, json
from pathlib import Path
from typing import List, Any
import aiohttp
from bs4 import BeautifulSoup
from core.config import config
from core.logger import get_logger
from core.models import DatasetEntry, DataSource, DownloadStatus

log = get_logger(__name__)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}

def _write_creds():
    if not (config.kaggle_username and config.kaggle_key): return
    p = Path.home() / ".kaggle" / "kaggle.json"
    if not p.exists():
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({"username": config.kaggle_username, "key": config.kaggle_key}))
        try: p.chmod(0o600)
        except: pass

def _get_api() -> Any:
    _write_creds()
    # Try KaggleApiExtended (old versions)
    try:
        from kaggle.api.kaggle_api_extended import KaggleApiExtended  # type: ignore
        api = KaggleApiExtended(); api.authenticate(); return api
    except: pass
    # Try KaggleApi (mid versions)
    try:
        from kaggle import KaggleApi  # type: ignore
        api = KaggleApi(); api.authenticate(); return api
    except: pass
    # Try module-level api (newest versions)
    try:
        import kaggle  # type: ignore
        if hasattr(kaggle, "api"): kaggle.api.authenticate(); return kaggle.api
    except: pass
    raise RuntimeError("Kaggle API init failed")

def _api_search(query: str, limit: int) -> List[DatasetEntry]:
    try:
        api = _get_api()
        # Try different argument names for different versions
        try:
            raw = api.dataset_list(search=query, page_size=limit)
        except TypeError:
            try:
                raw = api.dataset_list(search=query, max_size=None)
            except TypeError:
                raw = api.dataset_list(search=query)
        raw = list(raw)[:limit]
    except Exception as e:
        log.warning(f"Kaggle API search failed: {e}"); return []
    entries = []
    for ds in raw:
        ref = getattr(ds, "ref", "")
        entries.append(DatasetEntry(
            name=getattr(ds, "title", ref), description=getattr(ds, "subtitle", ""),
            source=DataSource.KAGGLE, download_url=f"https://www.kaggle.com/datasets/{ref}",
            data_type="tabular", download_status=DownloadStatus.PENDING,
            extra={"ref": ref, "votes": getattr(ds, "voteCount", 0)},
        ))
    return entries

async def _scrape_search(query: str, max_results: int) -> List[DatasetEntry]:
    url = f"https://www.kaggle.com/datasets?search={query.replace(' ', '+')}&sortBy=relevance"
    entries = []
    try:
        async with aiohttp.ClientSession(headers=_HEADERS) as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=25)) as r:
                html = await r.text()
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if script and script.string:
            data = json.loads(script.string)
            for ds in data.get("props",{}).get("pageProps",{}).get("datasets",[])[:max_results]:
                ref = ds.get("ref","")
                entries.append(DatasetEntry(
                    name=ds.get("title", ref), description=ds.get("subtitle",""),
                    source=DataSource.KAGGLE, download_url=f"https://www.kaggle.com/datasets/{ref}",
                    data_type="tabular", download_status=DownloadStatus.MANUAL_REQUIRED,
                ))
    except Exception as e:
        log.warning(f"Kaggle scrape failed: {e}")
    return entries

def _api_download(ref: str, dest: Path) -> str:
    try:
        api = _get_api()
        d = dest / ref.replace("/","__"); d.mkdir(parents=True, exist_ok=True)
        log.info(f"  ⬇  Kaggle download: {ref}")
        api.dataset_download_files(ref, path=str(d), unzip=True, quiet=False)
        return str(d)
    except Exception as e:
        log.warning(f"  Kaggle download failed: {e}"); return ""

async def search_and_download_kaggle(query: str, limit: int = 10, auto_download: bool = True) -> List[DatasetEntry]:
    loop = asyncio.get_event_loop()
    has_creds = bool(config.kaggle_username and config.kaggle_key)
    entries = await loop.run_in_executor(None, _api_search, query, limit) if has_creds else await _scrape_search(query, limit)
    log.info(f"Kaggle: found {len(entries)} datasets for '{query}'")
    if not (auto_download and has_creds):
        for e in entries: e.download_status = DownloadStatus.MANUAL_REQUIRED
        return entries
    dest = config.storage.datasets_dir / "kaggle"; dest.mkdir(parents=True, exist_ok=True)
    for entry in entries[:2]:
        ref = entry.extra.get("ref","")
        if ref:
            local = await loop.run_in_executor(None, _api_download, ref, dest)
            entry.local_path = local
            entry.download_status = DownloadStatus.SUCCESS if local else DownloadStatus.FAILED
    for entry in entries[2:]: entry.download_status = DownloadStatus.MANUAL_REQUIRED
    return entries