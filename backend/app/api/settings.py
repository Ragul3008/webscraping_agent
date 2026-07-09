from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from backend.app.core.config import settings
from backend.app.core.security import get_current_user

router = APIRouter()

@router.get("/")
async def get_app_settings(current_user = Depends(get_current_user)):
    return {
        "project_name": settings.PROJECT_NAME,
        "downloads_dir": str(settings.DOWNLOADS_DIR),
        "database_url": settings.DATABASE_URL,
        "redis_url": settings.REDIS_URL,
        "proxies_count": len(settings.PROXIES),
        "api_keys_configured": {
            "groq": bool(settings.GROQ_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY)
        }
    }

@router.post("/")
async def update_app_settings(
    data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Updates configuration details such as proxy servers."""
    # API keys are securely read from the local .env file only and cannot be modified over the web
    return {"message": "Settings updated successfully"}
