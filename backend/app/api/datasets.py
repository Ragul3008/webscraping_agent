import json
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Dataset, PreviewImage
from backend.app.services.ai_service import AIService
from backend.app.services.vector_service import VectorService
from backend.app.services.cv_service import CVService

router = APIRouter()
ai_service = AIService()
vector_service = VectorService()
cv_service = CVService()


@router.get("/")
async def list_datasets(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    return result.scalars().all()

@router.post("/")
async def create_dataset_record(
    data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Saves discovered dataset metadata to the database."""
    # Compute quality scores
    scores = ai_service.compute_dataset_scores(
        data.get("name", "Unknown"),
        data.get("description", ""),
        data.get("source", "Google Images")
    )
    
    # Create AI Recommendation schema
    recs = await ai_service.get_dataset_recommendation(
        data.get("name"),
        data.get("description")
    )
    
    dataset = Dataset(
        name=data.get("name"),
        description=data.get("description"),
        url=data.get("url"),
        source=data.get("source"),
        download_size=data.get("download_size", "Unknown"),
        license=scores.get("license"),
        popularity=scores.get("popularity"),
        quality_score=scores.get("quality_score"),
        trust_score=scores.get("trust_score"),
        duplicate_ratio=0.0,
        missing_labels=scores.get("missing_labels") == "yes",
        recommendations_json=json.dumps(recs),
        metadata_json=json.dumps(data.get("metadata", {}))
    )
    
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset

@router.get("/{id}")
async def get_dataset_details(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dataset).where(Dataset.id == id))
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Parse recommendations
    recs = {}
    if dataset.recommendations_json:
        try:
            recs = json.loads(dataset.recommendations_json)
        except Exception:
            pass
            
    return {
        "dataset": dataset,
        "recommendations": recs
    }

@router.get("/{id}/images")
async def get_dataset_images(
    id: int,
    tag: str | None = None,
    hide_blurry: bool = False,
    hide_duplicates: bool = False,
    nsfw_threshold: float = 0.5,
    min_width: int = 0,
    page: int = 1,
    limit: int = 30,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Paginated preview image query supporting real-time filter updates."""
    query = select(PreviewImage).where(PreviewImage.dataset_id == id)
    
    if hide_blurry:
        query = query.where(PreviewImage.blur_score >= 100.0)
    if hide_duplicates:
        # phash checks or direct flags
        pass
    if nsfw_threshold < 1.0:
        query = query.where(PreviewImage.nsfw_score <= nsfw_threshold)
    if min_width > 0:
        query = query.where(PreviewImage.width >= min_width)
        
    result = await db.execute(query.order_by(PreviewImage.id.asc()))
    images = result.scalars().all()
    
    # Filter by tags in memory (since tag list is stored as JSON array)
    if tag:
        tag_lower = tag.lower()
        filtered_images = []
        for img in images:
            if img.tags_json:
                try:
                    tags = json.loads(img.tags_json)
                    if any(t.lower() == tag_lower for t in tags):
                        filtered_images.append(img)
                except Exception:
                    pass
        images = filtered_images
        
    # Apply pagination offset
    offset = (page - 1) * limit
    paginated_images = images[offset:offset+limit]
    
    return {
        "images": paginated_images,
        "total": len(images),
        "page": page,
        "pages_count": (len(images) + limit - 1) // limit
    }

@router.post("/image/reverse-search")
async def reverse_image_search(
    file: UploadFile = File(...),
    top_k: int = 12,
    current_user = Depends(get_current_user)
):
    """Matches uploaded images against the FAISS vector database (Reverse Image Search)."""
    # Save file temporarily in storage
    temp_dir = settings.STORAGE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = temp_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    try:
        # Search similar vector representation
        matches = vector_service.search_similar_images(str(file_path), top_k=top_k)
        return matches
    finally:
        if file_path.exists():
            os.remove(file_path)
