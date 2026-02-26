from core.logger import setup_logger

logger = setup_logger("Planner")


class Planner:

    def next_step(self, state):

        # Step 1: Generate queries
        if not state.queries_generated:
            return "generate_queries"

        # Step 2: Search
        if not state.search_done:
            return "search"

        # Step 3: Select URLs
        if not state.urls_selected:

            # if no search results, stop safely
            if not state.search_results:
                logger.warning("No search results found. Completing task.")
                return "complete"

            return "select_urls"

        # Step 4: Scrape
        if not state.scrape_done:

            # if no URLs found, stop safely
            if not state.selected_urls:
                logger.warning("No URLs found. Completing task.")
                return "complete"

            return "scrape"

        # Step 5: Complete
        return "complete"