import os
from typing import List, Dict
from dotenv import load_dotenv

from core.logger import setup_logger
from agent.groq_llm import GroqLLM


# Load environment variables from .env
load_dotenv()

logger = setup_logger("LLMAgent")


class LLMAgent:
    """
    Autonomous LLM Agent powered by Groq LLaMA-3.3-70B.

    Responsibilities:
    - Generate optimized search queries
    - Select best dataset URLs
    - Validate scraped datasets
    """

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Please set it in .env file"
            )

        logger.info("Initializing LLaMA 3.3 70B Agent (Groq)")

        self.llm = GroqLLM(api_key=api_key)

    # --------------------------------------------------
    # Generate search queries
    # --------------------------------------------------

    def generate_search_queries(self, user_query: str) -> List[str]:

        logger.info("Generating optimized search queries")

        prompt = f"""
You are an expert dataset discovery agent.

Generate 5 highly relevant search queries to find datasets for:

{user_query}

Focus on:
- Kaggle
- HuggingFace
- GitHub
- Research datasets
- Open datasets

Return ONLY the queries, one per line.
Do NOT include numbering or explanations.
"""

        response = self.llm.chat(prompt)

        queries = [
            line.strip()
            for line in response.split("\n")
            if line.strip()
        ]

        logger.info(f"Generated {len(queries)} queries")

        return queries[:5]

    # --------------------------------------------------
    # Select best URLs
    # --------------------------------------------------

    def select_best_urls(
        self,
        search_results: List[Dict]
    ) -> List[str]:

        logger.info("Selecting best dataset URLs")

        if not search_results:
            return []

        formatted = "\n".join([
            f"{r.get('title','')} - {r.get('href','')}"
            for r in search_results
        ])

        prompt = f"""
You are an intelligent dataset selection agent.

Select the 5 BEST dataset URLs from this list:

{formatted}

Focus on:
- Kaggle
- HuggingFace
- GitHub
- Research datasets
- Direct dataset downloads

Return ONLY URLs, one per line.
"""

        response = self.llm.chat(prompt)

        urls = [
            line.strip()
            for line in response.split("\n")
            if line.startswith("http")
        ]

        logger.info(f"Selected {len(urls)} URLs")

        return urls[:5]

    # --------------------------------------------------
    # Validate dataset relevance
    # --------------------------------------------------

    def validate_dataset(self, dataset: Dict) -> bool:

        if not dataset:
            return False

        text = (
            dataset.get("dataset_name", "") +
            dataset.get("description", "")
        ).lower()

        keywords = [
            "dataset",
            "data",
            "download",
            "kaggle",
            "huggingface",
            "github",
            "research"
        ]

        return any(k in text for k in keywords)