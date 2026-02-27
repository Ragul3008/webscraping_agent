"""
Configuration management — reads from environment / .env file.
Import the module-level `config` singleton everywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class GroqConfig:
    api_key: str = ""
    model: str = "llama3-70b-8192"   # Best Groq model for tool-use / reasoning
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class AgentConfig:
    max_iterations: int = 20          # ReAct loop ceiling
    max_images: int = 40
    max_datasets_per_source: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_backoff: float = 1.5        # Exponential back-off multiplier
    concurrent_requests: int = 6


@dataclass
class StorageConfig:
    base_dir: Path = BASE_DIR
    images_dir: Path = BASE_DIR / "downloads" / "images"
    datasets_dir: Path = BASE_DIR / "downloads" / "datasets"
    results_dir: Path = BASE_DIR / "results"
    logs_dir: Path = BASE_DIR / "logs"

    def create_dirs(self) -> None:
        for d in [self.images_dir, self.datasets_dir, self.results_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    groq: GroqConfig = field(default_factory=GroqConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    # Third-party keys (optional)
    kaggle_username: str = ""
    kaggle_key: str = ""
    huggingface_token: str = ""
    serpapi_key: str = ""             # Optional – falls back to DuckDuckGo

    @classmethod
    def from_env(cls) -> "AppConfig":
        cfg = cls()
        cfg.groq.api_key = os.getenv("GROQ_API_KEY", "")
        cfg.groq.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")

        cfg.kaggle_username = os.getenv("KAGGLE_USERNAME", "")
        cfg.kaggle_key = os.getenv("KAGGLE_KEY", "")
        cfg.huggingface_token = os.getenv("HF_TOKEN", "")
        cfg.serpapi_key = os.getenv("SERPAPI_KEY", "")

        cfg.agent.max_images = int(os.getenv("MAX_IMAGES", "40"))
        cfg.agent.max_iterations = int(os.getenv("MAX_ITERATIONS", "20"))

        cfg.storage.create_dirs()
        return cfg


# ── Module-level singleton ────────────────────────────────────────────────────
config: AppConfig = AppConfig.from_env()
