from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "LLM Dataset Agent"
    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # openai, ollama, claude

    MAX_SEARCH_RESULTS: int = 10
    MAX_SCRAPE_CONCURRENCY: int = 5

    OUTPUT_DIR: str = "output"


settings = Settings()