import asyncio
from backend.app.tasks.celery_app import celery_app
from backend.app.services.download_service import DownloadService
from backend.app.core.logger import get_logger

logger = get_logger("CeleryTasks")

@celery_app.task(name="tasks.download_dataset_task")
def download_dataset_task(task_id: int):
    """Celery worker task that delegates execution to the async DownloadService."""
    logger.info(f"Celery worker picked up task {task_id}")
    downloader = DownloadService()
    try:
        asyncio.run(downloader.execute_download(task_id))
    except Exception as e:
        logger.error(f"Celery task failure for task {task_id}: {e}")
        raise e
