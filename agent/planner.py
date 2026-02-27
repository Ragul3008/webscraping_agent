"""
planner.py
──────────
Uses the Groq LLM to generate a structured search plan from the user's query.
Returns separate lists of search strategies per category.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List

from agent.groq_agent import GroqAgent
from core.logger import get_logger

log = get_logger(__name__)

_PLANNER_SYSTEM = """\
You are a dataset research planner. Given a user query, generate a JSON search
plan with the following keys:
{
  "intent": "<one sentence description of what the user wants>",
  "structured_dataset_queries": ["<query1>", "<query2>", ...],
  "image_search_queries": ["<query1>", "<query2>", ...],
  "video_dataset_queries": ["<query1>", "<query2>", ...],
  "priority_sources": ["huggingface", "kaggle", "uci", "github"],
  "notes": "<any special considerations>"
}

Generate 3–5 queries per category. Be specific and diverse.
"""


@dataclass
class SearchPlan:
    intent: str = ""
    structured_dataset_queries: List[str] = field(default_factory=list)
    image_search_queries: List[str] = field(default_factory=list)
    video_dataset_queries: List[str] = field(default_factory=list)
    priority_sources: List[str] = field(default_factory=list)
    notes: str = ""


class Planner:
    def __init__(self, agent: GroqAgent) -> None:
        self._agent = agent

    def create_plan(self, user_query: str) -> SearchPlan:
        """Ask the LLM to decompose the user query into a multi-strategy plan."""
        log.info(f"🗺  Planning search strategies for: '{user_query}'")

        messages = [
            {"role": "system", "content": _PLANNER_SYSTEM},
            {"role": "user", "content": f"User query: {user_query}"},
        ]
        raw = self._agent.chat(messages)
        log.debug(f"Planner LLM response:\n{raw}")

        plan = _parse_plan(raw, user_query)
        log.info(
            f"  Plan: {len(plan.structured_dataset_queries)} dataset queries, "
            f"{len(plan.image_search_queries)} image queries, "
            f"{len(plan.video_dataset_queries)} video queries"
        )
        log.info(f"  Priority sources: {plan.priority_sources}")
        return plan


def _parse_plan(raw: str, fallback_query: str) -> SearchPlan:
    text = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return _default_plan(fallback_query)

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return _default_plan(fallback_query)

    return SearchPlan(
        intent=data.get("intent", ""),
        structured_dataset_queries=data.get("structured_dataset_queries", [fallback_query]),
        image_search_queries=data.get("image_search_queries", [fallback_query + " image"]),
        video_dataset_queries=data.get("video_dataset_queries", [fallback_query + " video"]),
        priority_sources=data.get("priority_sources", ["huggingface", "kaggle", "uci", "github"]),
        notes=data.get("notes", ""),
    )


def _default_plan(query: str) -> SearchPlan:
    """Minimal fallback plan if the LLM fails to produce valid JSON."""
    return SearchPlan(
        intent=query,
        structured_dataset_queries=[query, f"{query} dataset download"],
        image_search_queries=[f"{query} image", f"{query} photo"],
        video_dataset_queries=[f"{query} video dataset"],
        priority_sources=["huggingface", "kaggle", "uci", "github"],
    )
