"""
groq_agent.py
─────────────
Low-level wrapper around the Groq API.
Provides:
  - chat()   — plain LLM call returning a string
  - decide() — structured JSON tool-selection call
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from groq import Groq  # type: ignore

from core.config import config
from core.logger import get_logger
from core.models import ToolCall

log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt injected into every request
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an autonomous AI agent specialised in discovering, evaluating, and \
downloading datasets and media from the internet. You reason step-by-step \
using the ReAct (Reasoning + Acting) framework.

Available tools:
  - web_search          : general web search
  - search_huggingface  : search HuggingFace Hub datasets
  - search_kaggle       : search Kaggle datasets
  - search_uci          : search UCI ML Repository
  - search_github       : search GitHub dataset repositories
  - download_images     : download images from Google/Bing (icrawler)
  - collect_video_links : collect video dataset links
  - finish              : return final answer (call when done)

IMPORTANT: You MUST always call download_images AND collect_video_links before calling finish.
Do NOT call finish until you have used both of these tools at least once.

When deciding the next action, respond ONLY with a single valid JSON object.
No extra text, no explanation outside the JSON, no multiple JSON objects.
Use this exact format:
{"thought": "your reasoning here", "tool_name": "tool_name_here", "arguments": {"query": "search query here"}, "reasoning": "one sentence justification"}

Rules:
- Always think before acting.
- If a tool returns no results, try a shorter, simpler alternative query.
- You MUST call download_images at least once.
- You MUST call collect_video_links at least once.
- Only call finish after images and video links have been collected.
- Never repeat the exact same tool call twice.
- Keep "thought" and "reasoning" values SHORT (under 20 words each) to avoid JSON issues.
- Do not use double quotes inside string values — use single quotes instead.
"""


class GroqAgent:
    """Thin wrapper around the Groq client."""

    def __init__(self) -> None:
        if not config.groq.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Please add it to your .env file."
            )
        self._client = Groq(api_key=config.groq.api_key)
        self._model = config.groq.model
        log.info(f"GroqAgent initialised — model: {self._model}")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Plain LLM call — returns the assistant message as a string."""
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=config.groq.temperature,
            max_tokens=config.groq.max_tokens,
        )
        return resp.choices[0].message.content or ""

    def decide(
        self,
        history: List[Dict[str, str]],
        observation: Optional[str] = None,
    ) -> ToolCall:
        """
        Ask the LLM to decide the next tool call.
        Parses the JSON response into a ToolCall object.
        """
        messages: List[Dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
        messages.extend(history)

        if observation:
            messages.append({"role": "user", "content": f"Observation:\n{observation}"})

        raw = self.chat(messages)
        log.debug(f"LLM raw response:\n{raw}")

        return _parse_tool_call(raw)


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing helper
# ─────────────────────────────────────────────────────────────────────────────

def _parse_tool_call(raw: str) -> ToolCall:
    """
    Extract JSON from LLM output using multiple fallback strategies.
    Handles markdown fences, extra text, multiple JSON objects, and
    truncated/malformed JSON.
    """
    # 1. Strip markdown fences
    text = re.sub(r"```(?:json)?```?", "", raw, flags=re.IGNORECASE).strip()
    text = re.sub(r"```", "", text).strip()

    # 2. Try to find ALL {...} blocks and pick the first valid one
    #    Use a bracket-matching approach to find complete JSON objects
    candidates = _extract_json_candidates(text)

    for candidate in candidates:
        try:
            data: Dict[str, Any] = json.loads(candidate)
            tool_name = data.get("tool_name", "")
            if tool_name:  # Valid tool call found
                return ToolCall(
                    tool_name=tool_name,
                    arguments=data.get("arguments", {}),
                    reasoning=data.get("reasoning", data.get("thought", "")),
                )
        except json.JSONDecodeError:
            continue

    # 3. Fallback: try regex extraction of key fields directly
    tool_match = re.search(r'"tool_name"\s*:\s*"([^"]+)"', text)
    if tool_match:
        tool_name = tool_match.group(1)
        # Extract query argument if present
        query_match = re.search(r'"query"\s*:\s*"([^"]+)"', text)
        arguments = {"query": query_match.group(1)} if query_match else {}
        log.debug(f"Recovered tool_name via regex: {tool_name}")
        return ToolCall(tool_name=tool_name, arguments=arguments, reasoning="recovered via regex")

    log.warning(f"Could not parse LLM response — raw:\n{raw[:300]}")
    return ToolCall(tool_name="download_images", arguments={}, reasoning="parse failed — forcing image download")


def _extract_json_candidates(text: str) -> list[str]:
    """
    Extract all {...} substrings from text using bracket matching.
    Returns them ordered from longest to shortest (most complete first).
    """
    candidates = []
    i = 0
    while i < len(text):
        if text[i] == "{":
            depth = 0
            j = i
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[i:j+1])
                        break
                j += 1
        i += 1
    # Sort: try the longest (most complete) candidate first
    candidates.sort(key=len, reverse=True)
    return candidates