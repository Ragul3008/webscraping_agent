import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict

from core.logger import setup_logger


logger = setup_logger("ScraperTool")


class ScraperTool:


    async def scrape_many(self, urls: List[str]) -> List[Dict]:

        logger.info(f"Starting async scrape for {len(urls)} URLs")

        async with aiohttp.ClientSession() as session:

            tasks = [
                self.scrape(session, url)
                for url in urls
            ]

            results = await asyncio.gather(*tasks)

        datasets = []

        for r in results:

            if r:
                datasets.append(r)

        logger.info(f"Scraping complete. Found {len(datasets)} datasets")

        return datasets


    async def scrape(self, session, url):

        try:

            async with session.get(url, timeout=30) as resp:

                if resp.status != 200:
                    return None

                html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")

                title = soup.title.string if soup.title else ""

                description = ""

                meta = soup.find("meta", attrs={"name": "description"})

                if meta:
                    description = meta.get("content", "")

                media_links = []

                for tag in soup.find_all("a", href=True):

                    href = tag["href"]

                    if any(ext in href.lower() for ext in [
                        ".jpg", ".png", ".jpeg",
                        ".mp4", ".avi",
                        ".zip", ".tar"
                    ]):
                        media_links.append(href)

                return {

                    "dataset_name": title,
                    "description": description,
                    "url": url,
                    "media_links": media_links

                }

        except Exception as e:

            logger.warning(f"Scrape failed {url}")

            return None