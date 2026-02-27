"""
Centralised logging — rich console output + rotating file handler.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / f"agent_{datetime.now():%Y%m%d_%H%M%S}.log"

_PLAIN_FMT = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

try:
    from rich.logging import RichHandler
    from rich.console import Console as RichConsole

    _rich_console = RichConsole(stderr=True)
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


def get_logger(name: str) -> logging.Logger:
    """Return (or reuse) a named logger with file + console handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Rotating file handler — keeps last 5 × 5 MB
    fh = RotatingFileHandler(
        _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_PLAIN_FMT)
    logger.addHandler(fh)

    # Console handler
    if _RICH_AVAILABLE:
        ch = RichHandler(
            console=_rich_console,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    else:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(_PLAIN_FMT)

    logger.addHandler(ch)
    return logger
