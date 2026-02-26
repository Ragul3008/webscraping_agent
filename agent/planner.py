from core.logger import get_logger

logger = get_logger("Planner")


class Planner:
    """
    Controls autonomous execution flow of the agent.
    """

    def next_step(self, state):

        if not state.queries_generated:

            return "generate_queries"

        elif not state.search_done:

            return "search"

        elif not state.urls_selected:

            return "select_urls"

        elif not state.scrape_done:

            return "scrape"

        elif not state.validation_done:

            return "validate"

        else:

            return "complete"