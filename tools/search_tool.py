from ddgs import DDGS
from core.logger import setup_logger

logger = setup_logger("SearchTool")


class SearchTool:

    def __init__(self):

        logger.info("SearchTool initialized")

    def search(self, query: str, max_results: int = 10):

        logger.info(f"Searching for: {query}")

        results = []

        try:

            with DDGS() as ddgs:

                for r in ddgs.text(query, max_results=max_results):

                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })

        except Exception as e:

            logger.error(f"Search failed: {e}")

        logger.info(f"Found {len(results)} results")

        return results