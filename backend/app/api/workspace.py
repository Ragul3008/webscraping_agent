from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from backend.app.core.db import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Project, SavedSearch, Bookmark

router = APIRouter()

@router.get("/projects")
async def list_projects(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.user_id == current_user.id))
    return result.scalars().all()

@router.post("/projects")
async def create_project(
    data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = Project(
        name=data.get("name"),
        description=data.get("description"),
        user_id=current_user.id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.get("/projects/{id}")
async def get_project_details(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve project along with bookmarks and saved searches
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.saved_searches),
            selectinload(Project.bookmarks)
        )
        .where(Project.id == id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Workspace project not found")
    return project

@router.post("/bookmarks")
async def add_bookmark(
    data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    bookmark = Bookmark(
        user_id=current_user.id,
        project_id=data.get("project_id"),
        dataset_id=data.get("dataset_id"),
        preview_image_id=data.get("preview_image_id")
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return bookmark

@router.get("/bookmarks")
async def get_bookmarks(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Bookmark).where(Bookmark.user_id == current_user.id))
    return result.scalars().all()

@router.delete("/bookmarks/{id}")
async def delete_bookmark(
    id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Bookmark).where(Bookmark.id == id, Bookmark.user_id == current_user.id))
    bookmark = result.scalars().first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
        
    await db.delete(bookmark)
    await db.commit()
    return {"message": "Bookmark removed"}
