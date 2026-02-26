import os
from typing import List, Dict
from dotenv import load_dotenv

from core.logger import setup_logger
from agent.groq_llm import GroqLLM


load_dotenv()

logger = setup_logger("LLMAgent")


class LLMAgent:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY missing")

        logger.info("Initializing LLaMA 3.3 70B Agent (Groq)")

        self.llm = GroqLLM(api_key=api_key)


    def generate_search_queries(self, user_query: str) -> List[str]:

        logger.info("Generating massive dataset search queries")

        prompt = f"""
You are a dataset discovery agent.

Generate 100 dataset search queries for:

{user_query}

STRICT RULES:

ONLY dataset queries
Include:

Kaggle
HuggingFace
GitHub
research datasets
image datasets
video datasets
zip datasets

Return ONLY queries.
One per line.
No numbering.
No explanation.
"""

        response = self.llm.chat(prompt)

        queries = []

        for line in response.split("\n"):

            line = line.strip()

            if len(line) > 10:
                queries.append(line)

        if len(queries) < 10:

            queries.extend([
                f"{user_query} dataset kaggle",
                f"{user_query} dataset github",
                f"{user_query} dataset huggingface",
                f"{user_query} dataset images download",
                f"{user_query} dataset videos download",
            ])

        logger.info(f"Generated {len(queries)} queries")

        return queries[:500]


    def select_best_urls(self, results: List[Dict]) -> List[str]:

        logger.info("Selecting best dataset URLs")

        urls = []

        for r in results:

            url = r.get("href")

            if not url:
                continue

            if any(domain in url.lower() for domain in [
                "kaggle",
                "huggingface",
                "github",
                "dataset",
                "data"
            ]):

                urls.append(url)

        return list(set(urls))[:50]


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
            "image",
            "video",
            "zip"
        ]

        return any(k in text for k in keywords)