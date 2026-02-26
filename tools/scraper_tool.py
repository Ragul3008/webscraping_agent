import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
from core.logger import get_logger

logger = get_logger("ScraperTool")


class ScraperTool:
    """
    Async dataset scraper.
    Extracts dataset info from webpages.
    """

    def __init__(self):

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        }

        logger.info("ScraperTool initialized")

    # ----------------------------------------------------
    # Fetch page
    # ----------------------------------------------------

    async def fetch(self, session, url):

        try:

            async with session.get(
                url,
                headers=self.headers,
                timeout=30,
            ) as response:

                if response.status != 200:

                    logger.warning(f"Failed fetch {url} status={response.status}")

                    return None

                return await response.text()

        except Exception as e:

            logger.warning(f"Fetch error {url}: {e}")

            return None

    # ----------------------------------------------------
    # Extract dataset info
    # ----------------------------------------------------

    def extract_dataset_info(self, url: str, html: str) -> Dict:

        soup = BeautifulSoup(html, "html.parser")

        title = ""

        if soup.title:
            title = soup.title.text.strip()

        description = ""

        meta = soup.find("meta", attrs={"name": "description"})

        if meta:
            description = meta.get("content", "")

        return {
            "dataset_name": title,
            "description": description,
            "download_url": url,
            "source": url,
        }

    # ----------------------------------------------------
    # Scrape single
    # ----------------------------------------------------

    async def scrape_one(self, session, url):

        logger.info(f"Scraping: {url}")

        html = await self.fetch(session, url)

        if not html:
            return None

        return self.extract_dataset_info(url, html)

    # ----------------------------------------------------
    # Scrape multiple
    # ----------------------------------------------------

    async def scrape_many(self, urls: List[str]) -> List[Dict]:

        logger.info(f"Starting async scrape for {len(urls)} URLs")

        results = []

        async with aiohttp.ClientSession() as session:

            tasks = [self.scrape_one(session, url) for url in urls]

            pages = await asyncio.gather(*tasks)

            for p in pages:

                if p:
                    results.append(p)

        logger.info(f"Scraping complete. Found {len(results)} datasets")

        return results