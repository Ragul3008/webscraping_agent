import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Dataset, PreviewImage

router = APIRouter()

@router.get("/dataset/{id}")
async def get_dataset_analytics(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Aggregates metrics for rendering visual charts on the frontend dashboard."""
    result = await db.execute(select(Dataset).where(Dataset.id == id))
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    img_result = await db.execute(select(PreviewImage).where(PreviewImage.dataset_id == id))
    images = img_result.scalars().all()
    
    # 1. Class / tag counts distribution
    class_counts = {}
    for img in images:
        if img.tags_json:
            try:
                tags = json.loads(img.tags_json)
                for t in tags:
                    class_counts[t] = class_counts.get(t, 0) + 1
            except Exception:
                pass
                
    class_distribution = [{"name": k, "value": v} for k, v in class_counts.items()]
    
    # 2. Resolution histogram
    resolutions = {"Low (< 300px)": 0, "SD (300px - 720px)": 0, "HD (720px - 1080px)": 0, "FHD+ (> 1080px)": 0}
    for img in images:
        max_dim = max(img.width, img.height)
        if max_dim < 300:
            resolutions["Low (< 300px)"] += 1
        elif max_dim < 720:
            resolutions["SD (300px - 720px)"] += 1
        elif max_dim <= 1080:
            resolutions["HD (720px - 1080px)"] += 1
        else:
            resolutions["FHD+ (> 1080px)"] += 1
            
    res_histogram = [{"resolution": k, "count": v} for k, v in resolutions.items()]
    
    # 3. Quality Breakdown
    blur_count = sum(1 for img in images if img.blur_score < 100.0)
    nsfw_count = sum(1 for img in images if img.nsfw_score > 0.5)
    
    return {
        "dataset_id": id,
        "total_images": len(images),
        "duplicate_ratio": dataset.duplicate_ratio,
        "class_distribution": class_distribution,
        "resolution_distribution": res_histogram,
        "quality_metrics": {
            "blurry_images": blur_count,
            "nsfw_images": nsfw_count,
            "clean_images": len(images) - blur_count - nsfw_count
        }
    }
