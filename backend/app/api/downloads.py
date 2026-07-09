from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.models import DownloadTask, Dataset
from backend.app.services.download_service import DownloadService

router = APIRouter()
download_service = DownloadService()

@router.post("/start")
async def start_download(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    dataset_id = data.get("dataset_id")
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset target not found")
        
    # Create download entry
    task = DownloadTask(
        user_id=current_user.id,
        dataset_id=dataset.id,
        status="PENDING",
        progress=0.0
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    try:
        from backend.app.tasks.tasks import download_dataset_task
        download_dataset_task.delay(task.id)
        dispatch_method = "Celery Worker Queue"
    except Exception:
        # Fallback to local FastAPI BackgroundTasks if Celery/Redis is offline
        background_tasks.add_task(download_service.execute_download, task.id)
        dispatch_method = "FastAPI Local Thread Pool"
        
    return {
        "message": "Download task queued successfully",
        "task_id": task.id,
        "dispatch_method": dispatch_method
    }

@router.get("/queue")
async def get_downloads_queue(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DownloadTask)
        .where(DownloadTask.user_id == current_user.id)
        .order_by(DownloadTask.created_at.desc())
    )
    return result.scalars().all()

@router.post("/{id}/pause")
async def pause_download(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DownloadTask).where(DownloadTask.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    success = download_service.pause_task(id)
    if success:
        task.status = "PAUSED"
        await db.commit()
        return {"status": "paused"}
    raise HTTPException(status_code=400, detail="Unable to pause task (it might not be running)")

@router.post("/{id}/resume")
async def resume_download(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DownloadTask).where(DownloadTask.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    success = download_service.resume_task(id)
    if success:
        task.status = "RUNNING"
        await db.commit()
        return {"status": "resumed"}
    raise HTTPException(status_code=400, detail="Unable to resume task")

@router.post("/{id}/cancel")
async def cancel_download(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DownloadTask).where(DownloadTask.id == id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    download_service.cancel_task(id)
    task.status = "FAILED"
    task.error_message = "Cancelled by user"
    await db.commit()
    return {"status": "cancelled"}
