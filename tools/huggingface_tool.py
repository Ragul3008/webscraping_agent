"""
huggingface_tool.py
───────────────────
Searches the HuggingFace Hub for datasets matching a query and
optionally downloads them via snapshot_download.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List

from core.config import config
from core.logger import get_logger
from core.models import DatasetEntry, DataSource, DownloadStatus

log = get_logger(__name__)


def _hf_search(query: str, limit: int) -> List[DatasetEntry]:
    """Synchronous HuggingFace dataset search."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        log.error("huggingface_hub not installed — pip install huggingface_hub")
        return []

    api = HfApi(token=config.huggingface_token or None)
    entries: List[DatasetEntry] = []
    try:
        datasets = list(
            api.list_datasets(search=query, limit=limit, full=True)
        )
        for ds in datasets:
            tags = list(ds.tags or [])
            entries.append(
                DatasetEntry(
                    name=ds.id,
                    description=getattr(ds, "description", "") or "",
                    source=DataSource.HUGGINGFACE,
                    download_url=f"https://huggingface.co/datasets/{ds.id}",
                    data_type=_infer_data_type(tags),
                    tags=tags,
                    download_status=DownloadStatus.PENDING,
                    extra={"likes": getattr(ds, "likes", 0)},
                )
            )
    except Exception as exc:
        log.warning(f"HuggingFace search error: {exc}")
    return entries


def _infer_data_type(tags: List[str]) -> str:
    tag_str = " ".join(t.lower() for t in tags)
    if "image" in tag_str or "vision" in tag_str:
        return "image"
    if "text" in tag_str or "nlp" in tag_str:
        return "text"
    if "audio" in tag_str or "speech" in tag_str:
        return "audio"
    if "video" in tag_str:
        return "video"
    return "unknown"


def _hf_download(dataset_id: str, dest_dir: Path) -> str:
    """Download a HuggingFace dataset snapshot to local disk."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        return ""

    local_dir = dest_dir / dataset_id.replace("/", "__")
    try:
        log.info(f"  ⬇  Downloading HF dataset: {dataset_id}")
        path = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=str(local_dir),
            token=config.huggingface_token or None,
            ignore_patterns=["*.bin", "*.pt", "*.safetensors"],  # skip model weights
        )
        log.info(f"  ✓  Saved to {path}")
        return str(path)
    except Exception as exc:
        log.warning(f"  HF download failed for {dataset_id}: {exc}")
        return ""


# ── Async wrappers ────────────────────────────────────────────────────────────

async def search_huggingface(query: str, limit: int = 10) -> List[DatasetEntry]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _hf_search, query, limit)


async def download_huggingface(dataset_id: str) -> str:
    dest = config.storage.datasets_dir / "huggingface"
    dest.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _hf_download, dataset_id, dest)


async def search_and_download(
    query: str,
    limit: int = 10,
    auto_download: bool = True,
) -> List[DatasetEntry]:
    """High-level: search HF, then attempt download on top results."""
    entries = await search_huggingface(query, limit)
    log.info(f"HuggingFace: found {len(entries)} datasets for '{query}'")

    if not auto_download:
        for e in entries:
            e.download_status = DownloadStatus.LINK_ONLY
        return entries

    for entry in entries[:3]:  # Auto-download top-3 to save time/disk
        local_path = await download_huggingface(entry.name)
        if local_path:
            entry.local_path = local_path
            entry.download_status = DownloadStatus.SUCCESS
        else:
            entry.download_status = DownloadStatus.MANUAL_REQUIRED

    # Remaining are link-only
    for entry in entries[3:]:
        entry.download_status = DownloadStatus.LINK_ONLY

    return entries
