"""
reasoning_loop.py
─────────────────
The heart of the autonomous agent.

Implements the ReAct loop:
    THINK → SELECT TOOL → EXECUTE TOOL → OBSERVE → REPEAT

The LLM controls which tool to call next. The loop runs until either:
  - The LLM calls the 'finish' tool
  - max_iterations is reached
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List

from agent.groq_agent import GroqAgent
from agent.planner import Planner, SearchPlan
from tools.search_tool import web_search
from tools.huggingface_tool import search_and_download as hf_search
from tools.kaggle_tool import search_and_download_kaggle
from tools.uci_scraper import search_uci, download_uci_dataset
from tools.github_scraper import search_github_datasets
from tools.image_downloader import download_images
from tools.video_dataset_collector import collect_video_links
from core.config import config
from core.logger import get_logger
from core.models import (
    AgentResult, AgentStep, DatasetEntry, DownloadStatus,
    ImageEntry, ToolCall, ToolResult, VideoDatasetLink,
)

log = get_logger(__name__)


class ReasoningLoop:
    """
    Orchestrates the full autonomous agent run for a given user query.
    """

    def __init__(self) -> None:
        self._llm = GroqAgent()
        self._planner = Planner(self._llm)

    # ─────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ─────────────────────────────────────────────────────────────────────────

    async def run(self, user_query: str) -> AgentResult:
        start = time.perf_counter()
        log.info(f"\n{'='*60}")
        log.info(f"🤖 Agent starting — query: '{user_query}'")
        log.info(f"{'='*60}\n")

        result = AgentResult(query=user_query)

        # ── Phase 1: Planning ─────────────────────────────────────────────────
        plan = self._planner.create_plan(user_query)

        # ── Phase 2: ReAct loop ───────────────────────────────────────────────
        history: List[Dict[str, str]] = [
            {
                "role": "user",
                "content": (
                    f"User query: {user_query}\n\n"
                    f"Search plan:\n{json.dumps(plan.__dict__, indent=2)}\n\n"
                    "Now execute the plan autonomously. "
                    "Collect datasets from all priority sources, download images, "
                    "collect video links, then call 'finish'."
                ),
            }
        ]

        used_tools: set = set()

        for iteration in range(config.agent.max_iterations):
            log.info(f"\n── Iteration {iteration + 1}/{config.agent.max_iterations} ──")

            # LLM decides next tool
            tool_call = self._llm.decide(history)
            log.info(f"  🧠 Thought: {tool_call.reasoning}")
            log.info(f"  🔧 Tool: {tool_call.tool_name}({json.dumps(tool_call.arguments)})")

            # Detect finish
            if tool_call.tool_name == "finish":
                log.info("  ✅ Agent signalled completion")
                break

            # Guard against infinite loops (same tool + same args)
            tool_key = f"{tool_call.tool_name}:{json.dumps(tool_call.arguments, sort_keys=True)}"
            if tool_key in used_tools:
                log.warning("  ⚠  Duplicate tool call detected — skipping")
                history.append(
                    {"role": "assistant", "content": json.dumps({"thought": tool_call.reasoning, "tool_name": tool_call.tool_name, "arguments": tool_call.arguments})}
                )
                history.append(
                    {"role": "user", "content": "Observation: Duplicate call skipped. Try a different tool or arguments."}
                )
                continue
            used_tools.add(tool_key)

            # Execute tool
            tool_result = await self._execute_tool(tool_call, result, plan)

            # Record step
            step = AgentStep(
                step_number=iteration + 1,
                thought=tool_call.reasoning,
                tool_call=tool_call,
                observation=tool_result.summary,
            )

            # Update conversation history
            history.append(
                {
                    "role": "assistant",
                    "content": json.dumps({
                        "thought": tool_call.reasoning,
                        "tool_name": tool_call.tool_name,
                        "arguments": tool_call.arguments,
                    }),
                }
            )
            history.append(
                {
                    "role": "user",
                    "content": f"Observation: {tool_result.summary}",
                }
            )

            result.steps_taken = iteration + 1

        # ── Phase 3: Guaranteed fallbacks ─────────────────────────────────────
        # If the LLM exited early without downloading images or video links,
        # force-run them here to ensure media is always collected.
        if not result.images_downloaded:
            log.info("🔄 Fallback: LLM skipped images — downloading now...")
            img_query = plan.image_search_queries[0] if plan.image_search_queries else user_query
            images = await download_images(query=img_query, max_num=config.agent.max_images)
            result.images_downloaded.extend(images)
            log.info(f"  Fallback images: {len(images)} downloaded")

        if not result.video_dataset_links:
            log.info("🔄 Fallback: LLM skipped videos — collecting links now...")
            vid_query = plan.video_dataset_queries[0] if plan.video_dataset_queries else user_query
            links = await collect_video_links(topic=vid_query)
            result.video_dataset_links.extend(links)
            log.info(f"  Fallback video links: {len(links)} collected")

        result.elapsed_seconds = round(time.perf_counter() - start, 2)
        log.info(
            f"\n✅ Agent finished in {result.elapsed_seconds}s — "
            f"{len(result.datasets)} datasets, "
            f"{len(result.images_downloaded)} images, "
            f"{len(result.video_dataset_links)} video links"
        )
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Tool execution dispatcher
    # ─────────────────────────────────────────────────────────────────────────

    async def _execute_tool(
        self,
        tool_call: ToolCall,
        result: AgentResult,
        plan: SearchPlan,
    ) -> ToolResult:
        """Route tool_call to the correct async tool function."""
        name = tool_call.tool_name
        args = tool_call.arguments

        try:
            if name == "web_search":
                data = await web_search(args.get("query", plan.structured_dataset_queries[0]))
                summary = f"web_search returned {len(data)} results"
                return ToolResult(tool_name=name, success=True, data=data, summary=summary)

            elif name == "search_huggingface":
                query = args.get("query", plan.structured_dataset_queries[0])
                auto = args.get("auto_download", True)
                entries = await hf_search(query=query, limit=config.agent.max_datasets_per_source, auto_download=auto)
                result.datasets.extend(entries)
                summary = f"HuggingFace: {len(entries)} datasets found"
                return ToolResult(tool_name=name, success=True, data=entries, summary=summary)

            elif name == "search_kaggle":
                query = args.get("query", plan.structured_dataset_queries[0])
                entries = await search_and_download_kaggle(query=query, limit=config.agent.max_datasets_per_source)
                result.datasets.extend(entries)
                summary = f"Kaggle: {len(entries)} datasets found"
                return ToolResult(tool_name=name, success=True, data=entries, summary=summary)

            elif name == "search_uci":
                query = args.get("query", plan.structured_dataset_queries[0])
                entries = await search_uci(query=query, limit=config.agent.max_datasets_per_source)
                # Try to download entries with direct links
                for entry in entries:
                    if entry.download_status == DownloadStatus.PENDING:
                        local = await download_uci_dataset(entry)
                        if local:
                            entry.local_path = local
                            entry.download_status = DownloadStatus.SUCCESS
                        else:
                            entry.download_status = DownloadStatus.MANUAL_REQUIRED
                result.datasets.extend(entries)
                summary = f"UCI: {len(entries)} datasets found"
                return ToolResult(tool_name=name, success=True, data=entries, summary=summary)

            elif name == "search_github":
                query = args.get("query", plan.structured_dataset_queries[0])
                entries = await search_github_datasets(query=query, limit=config.agent.max_datasets_per_source)
                result.datasets.extend(entries)
                summary = f"GitHub: {len(entries)} repos found"
                return ToolResult(tool_name=name, success=True, data=entries, summary=summary)

            elif name == "download_images":
                query = args.get("query", plan.image_search_queries[0] if plan.image_search_queries else plan.structured_dataset_queries[0])
                max_num = int(args.get("max_num", config.agent.max_images))
                images = await download_images(query=query, max_num=max_num)
                result.images_downloaded.extend(images)
                summary = f"Downloaded {len(images)} images for '{query}'"
                return ToolResult(tool_name=name, success=True, data=images, summary=summary)

            elif name == "collect_video_links":
                query = args.get("query", plan.video_dataset_queries[0] if plan.video_dataset_queries else plan.structured_dataset_queries[0])
                links = await collect_video_links(topic=query)
                result.video_dataset_links.extend(links)
                summary = f"Collected {len(links)} video dataset links"
                return ToolResult(tool_name=name, success=True, data=links, summary=summary)

            else:
                log.warning(f"  Unknown tool: {name}")
                return ToolResult(
                    tool_name=name, success=False,
                    error=f"Unknown tool '{name}'",
                    summary=f"Tool '{name}' not found",
                )

        except Exception as exc:
            log.error(f"  Tool '{name}' raised an exception: {exc}", exc_info=True)
            return ToolResult(
                tool_name=name, success=False,
                error=str(exc),
                summary=f"Error in {name}: {exc}",
            )