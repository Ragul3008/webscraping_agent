import asyncio
import os

from agent.llm_agent import LLMAgent
from agent.planner import Planner
from tools.search_tool import SearchTool
from tools.scraper_tool import ScraperTool

from storage.json_writer import write_json
from storage.csv_writer import write_csv

from agent.state import AgentState
from core.logger import setup_logger
from core.config import settings


logger = setup_logger("Main")


async def run_agent(user_query: str):

    logger.info(f"Starting agent for query: {user_query}")

    # initialize components
    agent = LLMAgent()
    planner = Planner()
    search_tool = SearchTool()
    scraper = ScraperTool()

    # initialize state
    state = AgentState(user_query=user_query)

    # main agent loop
    while not state.task_complete:

        step = planner.next_step(state)

        logger.info(f"Next step: {step}")

        # STEP 1: Generate queries
        if step == "generate_queries":

            state.search_queries = agent.generate_search_queries(
                state.user_query
            )

            state.queries_generated = True

            logger.info(
                f"Generated {len(state.search_queries)} queries"
            )


        # STEP 2: Search
        elif step == "search":

            for query in state.search_queries:

                results = search_tool.search(query)

                state.search_results.extend(results)

            state.search_done = True

            logger.info(
                f"Collected {len(state.search_results)} results"
            )


        # STEP 3: Select URLs
        elif step == "select_urls":

            state.selected_urls = agent.select_best_urls(
                state.search_results
            )

            state.urls_selected = True

            logger.info(
                f"Selected {len(state.selected_urls)} URLs"
            )


        # STEP 4: Scrape datasets
        elif step == "scrape":

            datasets = await scraper.scrape_many(
                state.selected_urls
            )

            # validate datasets
            state.datasets = [
                d for d in datasets
                if agent.validate_dataset(d)
            ]

            state.scrape_done = True
            state.validation_done = True

            logger.info(
                f"Validated {len(state.datasets)} datasets"
            )


        # STEP 5: Complete
        elif step == "complete":

            state.task_complete = True

            logger.info("Agent task completed")


    # save results
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    json_path = os.path.join(
        settings.OUTPUT_DIR,
        "datasets.json"
    )

    csv_path = os.path.join(
        settings.OUTPUT_DIR,
        "datasets.csv"
    )

    write_json(state.datasets, json_path)

    write_csv(state.datasets, csv_path)

    logger.info("Results saved successfully")

    return state.datasets


# entry point
if __name__ == "__main__":

    query = input("Enter dataset request: ")

    asyncio.run(run_agent(query))