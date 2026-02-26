import logging
from ddgs import DDGS

logger = logging.getLogger("SearchTool")


class SearchTool:

    def __init__(self):
        print("SearchTool ready")

    def search(self, query: str, max_results: int = 10):

        results_list = []

        try:

            with DDGS() as ddgs:

                results = ddgs.text(
                    query=query,
                    max_results=max_results
                )

                for r in results:

                    results_list.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")
                    })

        except Exception as e:

            logger.warning(f"Search error: {e}")

        return results_list