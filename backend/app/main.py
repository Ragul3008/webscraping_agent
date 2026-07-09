import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.core.db import engine, Base, AsyncSessionLocal
from backend.app.core.logger import get_logger
from backend.app.models import DownloadTask

# Import routers
from backend.app.api.auth import router as auth_router
from backend.app.api.search import router as search_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.downloads import router as downloads_router
from backend.app.api.workspace import router as workspace_router
from backend.app.api.chat import router as chat_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.admin import router as admin_router
from backend.app.api.settings import router as settings_router

logger = get_logger("MainApp")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SaaS AI-Powered Dataset Discovery & Download Platform API",
    version="1.0.0"
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup routine to create DB tables
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas initialized.")

# Mount downloads directory so the frontend can preview images
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(search_router, prefix=f"{settings.API_V1_STR}/search", tags=["Global & Semantic Search"])
app.include_router(datasets_router, prefix=f"{settings.API_V1_STR}/datasets", tags=["Dataset Manager"])
app.include_router(downloads_router, prefix=f"{settings.API_V1_STR}/downloads", tags=["Download Manager"])
app.include_router(workspace_router, prefix=f"{settings.API_V1_STR}/workspace", tags=["Workspace"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["AI Chat Assistant"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Dataset Analytics"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin Portal"])
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["Application Settings"])

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": f"Welcome to the {settings.PROJECT_NAME} API. Access docs at /docs"
    }

# Active WebSocket connections list
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

@app.websocket("/api/v1/ws/progress")
async def websocket_progress_endpoint(websocket: WebSocket):
    """WebSocket endpoint to broadcast active downloads progress in real time."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Poll DB every 1 second and send updates on active tasks
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(DownloadTask)
                    .where(DownloadTask.status.in_(["PENDING", "RUNNING", "PAUSED"]))
                )
                tasks = result.scalars().all()
                
                updates = []
                for t in tasks:
                    updates.append({
                        "task_id": t.id,
                        "dataset_id": t.dataset_id,
                        "status": t.status,
                        "progress": t.progress,
                        "speed": t.speed,
                        "eta": t.eta
                    })
                
                if updates:
                    await websocket.send_json({"tasks": updates})
                    
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
