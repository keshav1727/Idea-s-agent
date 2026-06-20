#!/usr/bin/env python3
"""ViralCryptoIdeas Dashboard — serves React frontend + API for pipeline control.

Usage:
    python dashboard.py              # starts on port 8050
    python dashboard.py --port 3000  # custom port
"""

from __future__ import annotations

import argparse
import json
import threading
import traceback
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
OUTPUT = ROOT / "output"

pipeline_state = {"running": False, "error": None}


def _scrape_and_analyze():
    """Shared: scrape all sources, filter, analyze patterns, save to disk."""
    from src.collectors import YouTubeCollector, RedditCollector, NewsCollector, TwitterCollector
    from src.analysis.patterns import analyze
    from src.schema import ContentItem

    collectors = {
        "youtube": YouTubeCollector,
        "reddit": RedditCollector,
        "news": NewsCollector,
        "twitter": TwitterCollector,
    }

    all_items: list[ContentItem] = []
    source_status: dict[str, str] = {}
    for name, cls in collectors.items():
        items = cls().collect()
        if items:
            all_items.extend(items)
            source_status[name] = f"{len(items)} items"
        else:
            source_status[name] = "unavailable"

    OUTPUT.mkdir(exist_ok=True)
    collected = sorted([i.to_dict() for i in all_items], key=lambda x: x["engagement_score"], reverse=True)
    _write_json(OUTPUT / "collected.json", collected)
    _write_json(OUTPUT / "source_status.json", source_status)

    patterns = analyze(all_items)
    _write_json(OUTPUT / "patterns.json", patterns.to_dict())

    return patterns, all_items


def run_pipeline() -> None:
    """Full pipeline: scrape → analyze → generate ideas with LLM."""
    from src.generator.content_ideas import generate_ideas
    from src.output.renderer import render_report

    print("\n[Pipeline] Scraping + analyzing...")
    patterns, items = _scrape_and_analyze()
    print(f"[Pipeline] {len(items)} items, {len(patterns.trending_narratives)} narratives\n")

    print("[Pipeline] Generating ideas with LLM...")
    ideas = generate_ideas(patterns)

    print("[Pipeline] Saving report...")
    render_report(patterns, ideas, str(ROOT / "report.md"))
    print(f"[Pipeline] Done.\n")


def refresh_data() -> None:
    """Scrape + analyze only — no LLM call."""
    print("\n[Refresh] Scraping fresh data...")
    patterns, items = _scrape_and_analyze()
    print(f"[Refresh] Done — {len(items)} items, {len(patterns.trending_narratives)} narratives\n")


def regenerate_section(section_key: str) -> None:
    """Regenerate one section of ideas using existing patterns."""
    from src.analysis.patterns import PatternReport
    from src.generator.content_ideas import (
        get_llm_client, _build_context, _call_with_retry,
        REEL_PROMPT, VIDEO_PROMPT, THREAD_PROMPT, HOOKS_PROMPT, SYSTEM_PROMPT,
    )

    patterns_path = OUTPUT / "patterns.json"
    ideas_path = OUTPUT / "ideas.json"
    if not patterns_path.exists():
        raise RuntimeError("No patterns data. Run full pipeline first.")

    with open(patterns_path) as f:
        patterns = PatternReport(**json.load(f))

    client, backend = get_llm_client()
    print(f"[Regenerate] {section_key} using {backend}")

    prompts = {
        "instagram_reels": (REEL_PROMPT, list),
        "youtube_videos": (VIDEO_PROMPT, list),
        "twitter_threads": (THREAD_PROMPT, list),
        "hooks_and_trends": (HOOKS_PROMPT, dict),
    }
    template, expected = prompts[section_key]
    result = _call_with_retry(client, template.format(context=_build_context(patterns)), expected)

    if result is None:
        raise RuntimeError(f"LLM failed to generate {section_key}")

    ideas = json.loads(ideas_path.read_text()) if ideas_path.exists() else {}

    if section_key == "hooks_and_trends":
        ideas["viral_hooks"] = result.get("viral_hooks", [])
        ideas["trending_web3_topics"] = result.get("trending_web3_topics", [])
    else:
        ideas[section_key] = result

    _write_json(ideas_path, ideas)
    print(f"[Regenerate] {section_key}: done")


def _write_json(path: Path, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── HTTP Server ──

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/ideas":
            self._serve_file(OUTPUT / "ideas.json", "application/json")
        elif self.path == "/api/patterns":
            self._serve_file(OUTPUT / "patterns.json", "application/json")
        elif self.path == "/api/collected":
            self._serve_file(OUTPUT / "collected.json", "application/json")
        elif self.path == "/api/source-status":
            self._serve_file(OUTPUT / "source_status.json", "application/json")
        elif self.path == "/api/status":
            self._send_json({"running": pipeline_state["running"], "error": pipeline_state["error"]})
        else:
            self._serve_frontend()

    def do_POST(self) -> None:
        routes = {
            "/api/generate": run_pipeline,
            "/api/generate/reels": lambda: regenerate_section("instagram_reels"),
            "/api/generate/videos": lambda: regenerate_section("youtube_videos"),
            "/api/generate/threads": lambda: regenerate_section("twitter_threads"),
            "/api/generate/hooks": lambda: regenerate_section("hooks_and_trends"),
            "/api/refresh": refresh_data,
        }
        fn = routes.get(self.path)
        if fn:
            self._run_in_background(fn)
        else:
            self.send_error(404)

    def _run_in_background(self, fn) -> None:
        if pipeline_state["running"]:
            self._send_json({"status": "already_running"}, 409)
            return
        pipeline_state["running"] = True
        pipeline_state["error"] = None

        def _run():
            try:
                fn()
                pipeline_state["error"] = None
            except Exception as e:
                pipeline_state["error"] = str(e)
                traceback.print_exc()
            finally:
                pipeline_state["running"] = False

        threading.Thread(target=_run, daemon=True).start()
        self._send_json({"status": "started"})

    def _serve_frontend(self) -> None:
        path = self.path.lstrip("/") or "index.html"
        file_path = FRONTEND_DIST / path
        if not file_path.exists() or not file_path.is_file():
            file_path = FRONTEND_DIST / "index.html"
        if not file_path.exists():
            self.send_error(404, "Frontend not built. Run: cd frontend && npm run build")
            return
        content_types = {
            ".html": "text/html", ".js": "application/javascript",
            ".css": "text/css", ".svg": "image/svg+xml",
            ".png": "image/png", ".ico": "image/x-icon",
        }
        self._serve_file(file_path, content_types.get(file_path.suffix, "application/octet-stream"))

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": f"Not found: {path.name}"}, 404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data: dict, code: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="ViralCryptoIdeas Dashboard")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)
    url = f"http://localhost:{args.port}"
    print(f"\n  ViralCryptoIdeas Dashboard")
    print(f"  Running at {url}")
    print(f"  Press Ctrl+C to stop\n")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
