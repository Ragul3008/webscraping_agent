"""
Shared Pydantic models — used by agent, tools, and storage layers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class DataSource(str, Enum):
    HUGGINGFACE = "huggingface"
    KAGGLE = "kaggle"
    UCI = "uci"
    GITHUB = "github"
    GOOGLE_IMAGES = "google_images"
    YOUTUBE = "youtube"
    GOVERNMENT = "government"
    RESEARCH = "research"
    OTHER = "other"


class DownloadStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_download_required"
    LINK_ONLY = "link_only"
    PENDING = "pending"


# ─────────────────────────────────────────────────────────────────────────────
# ReAct loop models
# ─────────────────────────────────────────────────────────────────────────────

class ToolCall(BaseModel):
    """A single tool invocation decided by the LLM."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


class ToolResult(BaseModel):
    """Result returned after executing a tool."""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    summary: str = ""


class AgentStep(BaseModel):
    """One complete ReAct cycle: Thought → Action → Observation."""
    step_number: int
    thought: str
    tool_call: Optional[ToolCall] = None
    observation: Optional[str] = None
    is_final: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Dataset / media models
# ─────────────────────────────────────────────────────────────────────────────

class DatasetEntry(BaseModel):
    """Metadata for a discovered or downloaded dataset."""
    name: str
    description: str = ""
    source: DataSource = DataSource.OTHER
    download_url: str = ""
    local_path: str = ""
    download_status: DownloadStatus = DownloadStatus.PENDING
    data_type: str = "unknown"
    size_mb: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ImageEntry(BaseModel):
    """A single downloaded image record."""
    filename: str
    local_path: str
    source_url: str = ""
    query: str = ""


class VideoDatasetLink(BaseModel):
    """A video dataset link (not downloaded — stored as reference)."""
    title: str
    url: str
    source: str = ""
    description: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Final aggregated output
# ─────────────────────────────────────────────────────────────────────────────

class AgentResult(BaseModel):
    """The complete structured output of one agent run."""
    query: str
    images_downloaded: List[ImageEntry] = Field(default_factory=list)
    video_dataset_links: List[VideoDatasetLink] = Field(default_factory=list)
    datasets: List[DatasetEntry] = Field(default_factory=list)
    steps_taken: int = 0
    elapsed_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None
