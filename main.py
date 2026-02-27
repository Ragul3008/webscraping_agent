"""
main.py
───────
Entry point for the Groq-Powered Autonomous Dataset & Media Acquisition Agent.

Usage:
    python main.py "banana plant disease dataset"
    python main.py --query "brain tumor MRI dataset" --max-images 50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from agent.reasoning_loop import ReasoningLoop
from core.config import config
from core.logger import get_logger
from storage.json_writer import save_json
from storage.csv_writer import save_csv

log = get_logger("main")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Groq-Powered Autonomous Dataset & Media Acquisition Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "banana plant disease dataset"
  python main.py --query "chest X-ray dataset" --max-images 60 --no-download
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Dataset search query (positional)",
    )
    parser.add_argument(
        "--query", "-q",
        dest="query_flag",
        help="Dataset search query (flag form)",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help=f"Maximum images to download (default: {config.agent.max_images})",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help=f"Maximum ReAct loop iterations (default: {config.agent.max_iterations})",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip actual file downloads (collect links only)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output only JSON, no CSV",
    )
    return parser.parse_args()


async def _run(query: str) -> None:
    loop = ReasoningLoop()
    result = await loop.run(query)

    # ── Persist results ───────────────────────────────────────────────────────
    json_path = save_json(result)
    if not _ARGS.json_only:
        csv_paths = save_csv(result)

    # ── Print summary to stdout ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("AGENT RESULTS SUMMARY")
    print("=" * 60)
    print(f"Query         : {result.query}")
    print(f"Steps taken   : {result.steps_taken}")
    print(f"Elapsed       : {result.elapsed_seconds}s")
    print(f"Datasets found: {len(result.datasets)}")
    print(f"Images saved  : {len(result.images_downloaded)}")
    print(f"Video links   : {len(result.video_dataset_links)}")
    print(f"JSON output   : {json_path}")
    print("=" * 60)

    if result.datasets:
        print("\n📚 TOP DATASETS:")
        for i, ds in enumerate(result.datasets[:10], 1):
            print(f"  {i:2}. [{ds.source.value:12s}] {ds.name}")
            if ds.description:
                print(f"       {ds.description[:80]}...")
            print(f"       URL: {ds.download_url}")
            print(f"       Status: {ds.download_status.value}")

    if result.video_dataset_links:
        print("\n🎥 VIDEO DATASET LINKS (top 5):")
        for lnk in result.video_dataset_links[:5]:
            print(f"  • [{lnk.source}] {lnk.title}")
            print(f"    {lnk.url}")

    if result.images_downloaded:
        print(f"\n🖼  Images saved to: {config.storage.images_dir}")

    print()


_ARGS: argparse.Namespace = argparse.Namespace(json_only=False)


def main() -> None:
    global _ARGS
    _ARGS = _parse_args()

    # Resolve query from positional or flag
    query = _ARGS.query or _ARGS.query_flag
    if not query:
        print("ERROR: Please provide a query.\n  python main.py \"banana plant disease dataset\"")
        sys.exit(1)

    # Override config values from CLI
    if _ARGS.max_images is not None:
        config.agent.max_images = _ARGS.max_images
    if _ARGS.max_iterations is not None:
        config.agent.max_iterations = _ARGS.max_iterations

    # Validate Groq API key
    if not config.groq.api_key:
        print(
            "ERROR: GROQ_API_KEY not found.\n"
            "  1. Get a free key at https://console.groq.com\n"
            "  2. Add it to .env:  GROQ_API_KEY=gsk_...\n"
        )
        sys.exit(1)

    asyncio.run(_run(query))


if __name__ == "__main__":
    main()
