"""
json_writer.py
──────────────
Serialises AgentResult to a timestamped JSON file in results/.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.config import config
from core.logger import get_logger
from core.models import AgentResult

log = get_logger(__name__)


def _make_filename(query: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in query)[:50]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{ts}.json"


def save_json(result: AgentResult) -> Path:
    """Write the full AgentResult as a pretty-printed JSON file."""
    dest = config.storage.results_dir / _make_filename(result.query)
    dest.parent.mkdir(parents=True, exist_ok=True)

    payload = result.model_dump(mode="json")   # Pydantic v2

    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"  📄 JSON saved → {dest}")
    return dest
