from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Dataset
from backend.app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatPayload(BaseModel):
    history: List[ChatMessage]
    message: str

@router.post("/dataset/{id}")
async def chat_dataset(
    id: int,
    payload: ChatPayload,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sends a chat message to the dataset AI assistant."""
    result = await db.execute(select(Dataset).where(Dataset.id == id))
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset context not found")
        
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]
    
    reply = await ai_service.chat_with_dataset(
        name=dataset.name,
        description=dataset.description or "",
        chat_history=history_dicts,
        user_message=payload.message
    )
    
    return {"reply": reply}
