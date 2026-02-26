from pydantic import BaseModel
from typing import List, Optional


class SearchResult(BaseModel):

    title: str

    url: str

    snippet: str


class DatasetInfo(BaseModel):

    dataset_name: str

    description: Optional[str] = None

    download_url: Optional[str] = None

    source: str


class AgentState(BaseModel):

    user_query: str

    search_queries: List[str] = []

    search_results: List[SearchResult] = []

    selected_urls: List[str] = []

    datasets: List[DatasetInfo] = []

    scrape_done: bool = False   # ✅ FIX ADDED

    task_complete: bool = False