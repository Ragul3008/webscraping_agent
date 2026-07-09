import os
import time
import asyncio
import httpx
from typing import List, Dict, Any, Callable
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logger import get_logger
from backend.app.core.db import AsyncSessionLocal
from backend.app.models import DownloadTask, Dataset, PreviewImage
from backend.app.services.cv_service import CVService
from backend.app.services.vector_service import VectorService

logger = get_logger("DownloadService")

# Active downloads cache for pausing/cancelling tasks in real time
active_tasks = {} # task_id -> {"cancel_event": asyncio.Event, "paused": bool}

class DownloadService:
    def __init__(self):
        self.cv_service = CVService()
        self.vector_service = VectorService()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def get_search_image_urls(self, query: str, limit: int = 40) -> List[str]:
        """Queries DuckDuckGo images and scrapes image links."""
        url = "https://html.duckduckgo.com/html/"
        urls = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=5.0) as client:
                resp = await client.post(url, data={"q": f"{query} images"})
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # DDG HTML image links parsing
                    for img in soup.find_all("img"):
                        src = img.get("src", "")
                        if "duckduckgo.com/iu/?u=" in src:
                            # Extract true URL from parameters
                            actual_url = src.split("?u=")[1].split("&")[0]
                            from urllib.parse import unquote
                            decoded_url = unquote(actual_url)
                            if decoded_url.startswith("http"):
                                urls.append(decoded_url)
                        if len(urls) >= limit:
                            break
        except Exception as e:
            logger.warning(f"Error scraping image search URLs: {e}")
            
        # Fallback urls if DuckDuckGo search is blocked
        if not urls:
            urls = [
                "https://images.unsplash.com/photo-1579353977828-2a4eab540b9a?q=80&w=600",
                "https://images.unsplash.com/photo-1541963463532-d68292c34b19?q=80&w=600",
                "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d?q=80&w=600",
                "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?q=80&w=600",
                "https://images.unsplash.com/photo-1472214222541-d510753a8707?q=80&w=600"
            ]
        return urls[:limit]

    async def execute_download(self, task_id: int, on_progress: Callable[[float, str, str], Any] = None):
        """Routes download task to either image crawling or platform ZIP archive downloading."""
        async with AsyncSessionLocal() as db:
            task_query = await db.execute(select(DownloadTask).where(DownloadTask.id == task_id))
            task = task_query.scalars().first()
            if not task:
                return

            dataset_query = await db.execute(select(Dataset).where(Dataset.id == task.dataset_id))
            dataset = dataset_query.scalars().first()
            if not dataset:
                return

            is_image_crawler = dataset.source in ["Google Images", "Bing Images", "DuckDuckGo Images", "Aggregated Hub"]
            if is_image_crawler:
                await self.download_image_task(task_id, on_progress)
            else:
                await self.download_archive_task(task_id, on_progress)

    async def download_image_task(self, task_id: int, on_progress: Callable[[float, str, str], Any] = None):
        """Asynchronously downloads images, applies CV filters, captioning, and inserts vectors."""
        async with AsyncSessionLocal() as db:
            task_query = await db.execute(select(DownloadTask).where(DownloadTask.id == task_id))
            task = task_query.scalars().first()
            if not task:
                logger.error(f"Download Task {task_id} not found.")
                return

            dataset_query = await db.execute(select(Dataset).where(Dataset.id == task.dataset_id))
            dataset = dataset_query.scalars().first()
            if not dataset:
                logger.error(f"Dataset {task.dataset_id} not found.")
                return

            # Setup directory
            dataset_dir = settings.DATASETS_DIR / str(dataset.id)
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            task.status = "RUNNING"
            await db.commit()

            # Register active task events for pause/cancel
            cancel_event = asyncio.Event()
            active_tasks[task_id] = {"cancel_event": cancel_event, "paused": False}
            
            # Retrieve urls to download
            urls = await self.get_search_image_urls(dataset.name, limit=40)
            total_images = len(urls)
            downloaded_count = 0
            duplicate_count = 0
            
            logger.info(f"Starting downloads for dataset {dataset.name} — {total_images} urls found.")
            
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
                for idx, img_url in enumerate(urls):
                    # Check cancel/pause state
                    if cancel_event.is_set():
                        task.status = "FAILED"
                        task.error_message = "Cancelled by user"
                        await db.commit()
                        break
                        
                    while active_tasks[task_id]["paused"]:
                        # Pause task loop
                        task.status = "PAUSED"
                        task.speed = "0 KB/s"
                        await db.commit()
                        await asyncio.sleep(1.0)
                        if cancel_event.is_set():
                            break
                    
                    if task.status == "PAUSED":
                        task.status = "RUNNING"
                        await db.commit()
                        
                    try:
                        start_time = time.time()
                        # Download single image
                        resp = await client.get(img_url)
                        if resp.status_code != 200:
                            continue
                            
                        # Save image
                        file_ext = img_url.split(".")[-1].split("?")[0]
                        if len(file_ext) > 4 or len(file_ext) < 2:
                            file_ext = "jpg"
                        
                        file_name = f"image_{idx+1}.{file_ext}"
                        local_path = dataset_dir / file_name
                        
                        with open(local_path, "wb") as f:
                            f.write(resp.content)
                            
                        # Calculate speeds & ETA
                        file_size_kb = len(resp.content) / 1024
                        elapsed = time.time() - start_time
                        kb_per_sec = file_size_kb / elapsed if elapsed > 0 else file_size_kb
                        speed_str = f"{round(kb_per_sec, 1)} KB/s"
                        
                        # Filter parameters: Dimensions & Blurriness
                        w, h = self.cv_service.get_image_dimensions(str(local_path))
                        if w < 100 or h < 100:
                            # Reject tiny images
                            os.remove(local_path)
                            continue
                            
                        is_blur, blur_score = self.cv_service.is_image_blurry(str(local_path))
                        nsfw_score, is_watermark = self.cv_service.check_nsfw_and_watermark(str(local_path))
                        phash = self.cv_service.compute_phash(str(local_path))
                        
                        # Check duplicate
                        existing_phash = await db.execute(
                            select(PreviewImage).where(
                                PreviewImage.dataset_id == dataset.id,
                                PreviewImage.phash == phash
                            )
                        )
                        if existing_phash.scalars().first():
                            # Duplicate found, delete
                            os.remove(local_path)
                            duplicate_count += 1
                            continue
                        
                        # Generate caption & tags using fallback or Gemini
                        caption, tags = await self.cv_service.generate_caption_and_tags(str(local_path))
                        
                        # Insert database preview
                        preview = PreviewImage(
                            dataset_id=dataset.id,
                            image_url=img_url,
                            local_path=str(local_path),
                            caption=caption,
                            tags_json=json.dumps(tags),
                            phash=phash,
                            nsfw_score=nsfw_score,
                            blur_score=blur_score,
                            width=w,
                            height=h
                        )
                        db.add(preview)
                        await db.flush() # Populate preview.id
                        
                        # Index in vector search
                        self.vector_service.add_image_vector(preview.id, dataset.id, str(local_path))
                        
                        # Update task status
                        downloaded_count += 1
                        progress = round((idx + 1) / total_images * 100, 1)
                        
                        # Estimate remaining
                        remaining_images = total_images - (idx + 1)
                        eta_sec = int(remaining_images * elapsed)
                        eta_str = f"{eta_sec}s" if eta_sec > 0 else "0s"
                        
                        task.progress = progress
                        task.speed = speed_str
                        task.eta = eta_str
                        
                        # Callback function for WebSockets progress broadcast
                        if on_progress:
                            await on_progress(progress, speed_str, eta_str)
                            
                        await db.commit()
                        
                    except Exception as e:
                        logger.warning(f"Failed to download image {img_url}: {e}")
                        
            # Finalize task
            if task.status == "RUNNING":
                task.status = "COMPLETED"
                task.progress = 100.0
                task.speed = "0 KB/s"
                task.eta = "Completed"
                
                # Update dataset analytics numbers
                dataset.image_count = downloaded_count
                if downloaded_count > 0:
                    dataset.duplicate_ratio = round((duplicate_count / (downloaded_count + duplicate_count)) * 100, 1)
                await db.commit()
                
            active_tasks.pop(task_id, None)
            logger.info(f"Task {task_id} completed. Added {downloaded_count} preview images.")

    async def download_archive_task(self, task_id: int, on_progress: Callable[[float, str, str], Any] = None):
        """Downloads raw dataset files and ZIP archives from HuggingFace, GitHub, Zenodo, Figshare, UCI, etc."""
        import zipfile
        import shutil
        
        async with AsyncSessionLocal() as db:
            task_query = await db.execute(select(DownloadTask).where(DownloadTask.id == task_id))
            task = task_query.scalars().first()
            if not task:
                return

            dataset_query = await db.execute(select(Dataset).where(Dataset.id == task.dataset_id))
            dataset = dataset_query.scalars().first()
            if not dataset:
                return

            # Directory configuration
            dataset_dir = settings.DATASETS_DIR / str(dataset.id)
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            task.status = "RUNNING"
            await db.commit()

            cancel_event = asyncio.Event()
            active_tasks[task_id] = {"cancel_event": cancel_event, "paused": False}

            # Determine direct download link based on repository source
            url = dataset.url
            source = dataset.source
            file_name = "dataset_archive.zip"
            
            # Rewrite paths for direct downloads from platforms
            if "github.com" in url.lower():
                parts = url.replace("https://github.com/", "").split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
                    file_name = f"{repo}_main.zip"
            elif "zenodo.org" in url.lower() and "/record/" in url:
                record_id = url.split("/record/")[-1]
                url = f"https://zenodo.org/api/records/{record_id}"
                try:
                    async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            files = resp.json().get("files", [])
                            if files:
                                url = files[0].get("links", {}).get("self", dataset.url)
                                file_name = files[0].get("key", "zenodo_dataset.zip")
                except Exception:
                    url = dataset.url
            elif "openml.org" in url.lower() and "/d/" in url:
                dataset_id = url.split("/d/")[-1]
                url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
                
            archive_path = dataset_dir / file_name
            logger.info(f"Downloading raw dataset archive from: {url}")
            
            try:
                start_time = time.time()
                bytes_downloaded = 0
                
                async with httpx.AsyncClient(headers=self.headers, timeout=60.0) as client:
                    async with client.stream("GET", url) as response:
                        if response.status_code != 200:
                            response = await client.get(dataset.url)
                            with open(archive_path, "wb") as f:
                                f.write(response.content)
                            bytes_downloaded = len(response.content)
                        else:
                            total_size = int(response.headers.get("Content-Length", 0))
                            with open(archive_path, "wb") as f:
                                async for chunk in response.iter_bytes(chunk_size=8192):
                                    if cancel_event.is_set():
                                        break
                                    while active_tasks[task_id]["paused"]:
                                        await asyncio.sleep(1.0)
                                        if cancel_event.is_set():
                                            break
                                            
                                    f.write(chunk)
                                    bytes_downloaded += len(chunk)
                                    
                                    # Update progress metrics
                                    if total_size > 0:
                                        progress = round((bytes_downloaded / total_size) * 100, 1)
                                        elapsed = time.time() - start_time
                                        speed_kb = (bytes_downloaded / 1024) / elapsed if elapsed > 0 else 0
                                        speed_str = f"{round(speed_kb, 1)} KB/s"
                                        eta_sec = int((total_size - bytes_downloaded) / (speed_kb * 1024)) if speed_kb > 0 else 0
                                        
                                        task.progress = progress
                                        task.speed = speed_str
                                        task.eta = f"{eta_sec}s"
                                        if on_progress:
                                            await on_progress(progress, speed_str, f"{eta_sec}s")
                                        await db.commit()
                                        
                if cancel_event.is_set():
                    task.status = "FAILED"
                    task.error_message = "Cancelled by user"
                    await db.commit()
                    active_tasks.pop(task_id, None)
                    return

                # If zip file, unpack it
                if zipfile.is_zipfile(archive_path):
                    logger.info(f"Unzipping dataset archive: {archive_path}")
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(dataset_dir)
                    os.remove(archive_path)
                    
                task.status = "COMPLETED"
                task.progress = 100.0
                task.speed = "0 KB/s"
                task.eta = "Completed"
                
                # Scan directory for preview images to list
                img_count = 0
                for root, _, files in os.walk(dataset_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            img_count += 1
                            
                dataset.image_count = img_count
                dataset.download_size = f"{round(bytes_downloaded / (1024 * 1024), 1)} MB"
                await db.commit()
                logger.info(f"Platform Archive Task {task_id} completed. Downloaded {dataset.download_size}.")
                
            except Exception as e:
                logger.error(f"Archive download failed: {e}")
                task.status = "FAILED"
                task.error_message = str(e)
                await db.commit()
                
            active_tasks.pop(task_id, None)

    def pause_task(self, task_id: int):
        if task_id in active_tasks:
            active_tasks[task_id]["paused"] = True
            return True
        return False

    def resume_task(self, task_id: int):
        if task_id in active_tasks:
            active_tasks[task_id]["paused"] = False
            return True
        return False

    def cancel_task(self, task_id: int):
        if task_id in active_tasks:
            active_tasks[task_id]["cancel_event"].set()
            return True
        return False
import json
