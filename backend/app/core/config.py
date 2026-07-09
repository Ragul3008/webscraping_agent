import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings:
    PROJECT_NAME: str = "Webscrapping Agent"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./platform.db")
    
    # Celery + Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Hub Credentials
    KAGGLE_USERNAME: str = os.getenv("KAGGLE_USERNAME", "")
    KAGGLE_KEY: str = os.getenv("KAGGLE_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # Storage Paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    DOWNLOADS_DIR: Path = STORAGE_DIR / "downloads"
    IMAGES_DIR: Path = DOWNLOADS_DIR / "images"
    DATASETS_DIR: Path = DOWNLOADS_DIR / "datasets"
    
    # Proxy rotation list (comma-separated in env)
    PROXIES: list[str] = [p.strip() for p in os.getenv("PROXIES", "").split(",") if p.strip()]

    def create_directories(self):
        for path in [self.STORAGE_DIR, self.DOWNLOADS_DIR, self.IMAGES_DIR, self.DATASETS_DIR]:
            path.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.create_directories()
