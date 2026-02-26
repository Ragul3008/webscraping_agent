from pydantic import BaseModel, Field
from typing import List, Dict


class AgentState(BaseModel):

    # user input
    user_query: str

    # generated queries
    search_queries: List[str] = Field(default_factory=list)

    # raw search results
    search_results: List[Dict] = Field(default_factory=list)

    # selected URLs
    selected_urls: List[str] = Field(default_factory=list)

    # scraped datasets
    datasets: List[Dict] = Field(default_factory=list)

    # control flags
    queries_generated: bool = False
    search_done: bool = False
    urls_selected: bool = False
    scrape_done: bool = False
    validation_done: bool = False

    # THIS is the missing field
    task_complete: bool = False