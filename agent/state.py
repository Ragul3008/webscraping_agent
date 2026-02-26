from pydantic import BaseModel, Field
from typing import List, Dict


class AgentState(BaseModel):

    user_query: str

    search_queries: List[str] = Field(default_factory=list)

    search_results: List[Dict] = Field(default_factory=list)

    selected_urls: List[str] = Field(default_factory=list)

    datasets: List[Dict] = Field(default_factory=list)

    queries_generated: bool = False

    search_done: bool = False

    urls_selected: bool = False

    scrape_done: bool = False

    download_done: bool = False

    task_complete: bool = False