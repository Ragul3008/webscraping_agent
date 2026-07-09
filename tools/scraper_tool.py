import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
from core.logger import setup_logger


logger = setup_logger("ScraperTool")


class ScraperTool:

    async def scrape_many(self, urls: List[str]) -> List[Dict]:

        if not urls:
            return []

        logger.info(f"Starting async scrape for {len(urls)} URLs")

        timeout = aiohttp.ClientTimeout(total=20)

        connector = aiohttp.TCPConnector(limit=10)

        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        ) as session:

            tasks = [
                self.scrape(session, url)
                for url in urls
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        datasets = []

        for r in results:

            if isinstance(r, dict):
                datasets.append(r)

        logger.info(f"Scraping complete. Found {len(datasets)} datasets")

        return datasets


    async def scrape(self, session, url):

        try:

            async with session.get(url) as resp:

                if resp.status != 200:
                    return None

                content_type = resp.headers.get("Content-Type", "")

                if "text/html" not in content_type:
                    return None

                html = await resp.text(errors="ignore")

                soup = BeautifulSoup(html, "html.parser")

                title = soup.title.string.strip() if soup.title else ""

                description = ""

                meta = soup.find("meta", attrs={"name": "description"})

                if meta:
                    description = meta.get("content", "").strip()

                media_links = []

                for tag in soup.find_all("a", href=True):

                    href = tag["href"]

                    if any(ext in href.lower() for ext in [
                        ".jpg", ".png", ".jpeg",
                        ".mp4", ".avi", ".mov",
                        ".zip", ".tar", ".gz",
                        ".csv", ".json"
                    ]):
                        media_links.append(href)

                # Only return meaningful dataset pages
                if not title and not media_links:
                    return None

                return {
                    "dataset_name": title,
                    "description": description,
                    "url": url,
                    "media_links": list(set(media_links))
                }

        except asyncio.TimeoutError:
            logger.warning(f"Timeout while scraping {url}")
            return None

        except Exception:
            logger.warning(f"Scrape failed {url}")
            return None