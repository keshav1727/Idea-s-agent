#!/usr/bin/env python3
"""
ViralCryptoIdeas — CLI entrypoint.

Runs the full 4-stage pipeline:
  1. Collect viral crypto content from YouTube, Reddit, News, Social
  2. Analyze patterns (hooks, topics, narratives, structures)
  3. Generate content ideas via LLM (Ollama / OpenAI)
  4. Render Markdown report + JSON outputs

Usage:
    python main.py
    python main.py --sources youtube,reddit,news,twitter --output report.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.collectors import YouTubeCollector, RedditCollector, NewsCollector, TwitterCollector
from src.analysis.patterns import analyze
from src.generator.content_ideas import generate_ideas
from src.output.renderer import render_report
from src.schema import ContentItem

COLLECTORS = {
    "youtube": YouTubeCollector,
    "reddit": RedditCollector,
    "news": NewsCollector,
    "twitter": TwitterCollector,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate viral crypto content ideas using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python main.py --sources youtube,reddit,news --output report.md",
    )
    parser.add_argument(
        "--sources", type=str, default="youtube,reddit,news,twitter",
        help="Comma-separated data sources (default: youtube,reddit,news,twitter)",
    )
    parser.add_argument(
        "--output", type=str, default="report.md",
        help="Output report path (default: report.md)",
    )
    args = parser.parse_args()

    sources = [s.strip().lower() for s in args.sources.split(",")]
    invalid = [s for s in sources if s not in COLLECTORS]
    if invalid:
        print(f"Error: Unknown sources: {', '.join(invalid)}")
        print(f"Available: {', '.join(COLLECTORS.keys())}")
        sys.exit(1)

    start = time.time()
    print("=" * 60)
    print("  ViralCryptoIdeas — AI Content Strategy Engine")
    print("=" * 60)

    # ── Stage 1: Collect ──
    print("\n[Stage 1/4] Collecting viral crypto content...")
    all_items: list[ContentItem] = []
    for source in sources:
        collector = COLLECTORS[source]()
        all_items.extend(collector.collect())
    print(f"  Total: {len(all_items)} items collected")

    output_dir = Path(args.output).parent / "output"
    output_dir.mkdir(exist_ok=True)
    collected = sorted(
        [item.to_dict() for item in all_items],
        key=lambda x: x["engagement_score"],
        reverse=True,
    )
    with open(output_dir / "collected.json", "w") as f:
        json.dump(collected, f, indent=2, default=str)
    print(f"  Saved raw data → {output_dir / 'collected.json'}\n")

    # ── Stage 2: Analyze ──
    print("[Stage 2/4] Analyzing patterns...")
    patterns = analyze(all_items)
    print(f"  {len(patterns.viral_hooks)} hook categories, "
          f"{len(patterns.trending_narratives)} narratives, "
          f"{len(patterns.storytelling_structures)} structures, "
          f"{len(patterns.popular_topics)} keywords\n")

    # ── Stage 3: Generate ──
    print("[Stage 3/4] Generating content ideas...")
    ideas = generate_ideas(patterns)
    print()

    # ── Stage 4: Output ──
    print("[Stage 4/4] Rendering report...")
    render_report(patterns, ideas, args.output)
    print()

    elapsed = time.time() - start
    print("=" * 60)
    print(f"  Done in {elapsed:.1f}s")
    print(f"  Report  → {args.output}")
    print(f"  JSON    → output/patterns.json, output/ideas.json")
    print(f"  Raw     → output/collected.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
