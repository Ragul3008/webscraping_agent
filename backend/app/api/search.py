from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.services.search_service import SearchService
from backend.app.services.vector_service import VectorService
from backend.app.models import SavedSearch

router = APIRouter()
search_service = SearchService()
vector_service = VectorService()

@router.get("/")
async def global_search(
    query: str, 
    project_id: int | None = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes multi-source search in parallel for HuggingFace, GitHub, Roboflow, Zenodo, Figshare, etc."""
    results = await search_service.search_all(query)
    
    # Save searches if project context is available
    if project_id:
        saved_search = SavedSearch(
            project_id=project_id,
            query=query,
            results_count=len(results)
        )
        db.add(saved_search)
        await db.commit()
        
    return results

@router.get("/semantic")
async def semantic_search(
    query: str,
    top_k: int = 15,
    current_user = Depends(get_current_user)
):
    """Semantic natural language search across local images index via vector embeddings."""
    matches = vector_service.search_semantic(query, top_k=top_k)
    return matches
