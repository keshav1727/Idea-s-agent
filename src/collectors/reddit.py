"""Reddit collector — scrapes old.reddit.com HTML for real engagement data."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

from src.schema import ContentItem, normalize_engagement
from src.collectors.base import BaseCollector

SUBREDDITS = ["CryptoCurrency", "Bitcoin", "ethereum"]
SORT_MODES = [("top", "?t=month")]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


class RedditCollector(BaseCollector):
    platform = "reddit"

    def fetch_live(self) -> list[ContentItem]:
        items: list[ContentItem] = []
        seen_titles: set[str] = set()
        session = requests.Session()
        session.headers.update(HEADERS)

        for i, sub in enumerate(SUBREDDITS):
            if i > 0:
                time.sleep(3)
            for sort, params in SORT_MODES:
                url = f"https://old.reddit.com/r/{sub}/{sort}/{params}"
                try:
                    resp = session.get(url, timeout=15)
                    resp.raise_for_status()
                except Exception as e:
                    print(f"    [reddit] r/{sub}/{sort} failed: {e}")
                    continue

                posts = _parse_listing_html(resp.text, sub)
                for post in posts:
                    if post["title"] in seen_titles:
                        continue
                    if post["title"].lower().startswith(("daily", "weekly", "monthly")):
                        continue
                    seen_titles.add(post["title"])

                    metrics = {
                        "score": post["score"],
                        "num_comments": post["num_comments"],
                    }
                    items.append(ContentItem(
                        platform="reddit",
                        title=post["title"],
                        url=f"https://reddit.com{post['permalink']}",
                        engagement_raw=metrics,
                        engagement_score=normalize_engagement("reddit", metrics),
                        published_at=post["published_at"],
                        source_keywords=_extract_keywords(post["title"]),
                        description=post["title"],
                    ))

        if not items:
            raise ValueError("No Reddit posts scraped")
        return items

    def _parse_sample(self, raw: list[dict]) -> list[ContentItem]:
        return []


def _parse_listing_html(html: str, subreddit: str) -> list[dict]:
    """Extract posts with real scores and comment counts from old.reddit HTML."""
    posts: list[dict] = []

    scores = re.findall(r'data-score="(\d+)"', html)
    permalinks = re.findall(r'data-permalink="([^"]+)"', html)
    timestamps = re.findall(r'data-timestamp="(\d+)"', html)
    titles = re.findall(
        r'<a[^>]*class="[^"]*title[^"]*may-blank[^"]*"[^>]*>([^<]+)</a>', html
    )
    comment_counts = re.findall(r'>(\d+)\s+comments?</a>', html)

    count = min(len(scores), len(titles), len(permalinks))
    for i in range(count):
        ts_ms = int(timestamps[i]) if i < len(timestamps) else 0
        published = ""
        if ts_ms:
            published = datetime.fromtimestamp(
                ts_ms / 1000, tz=timezone.utc
            ).isoformat()

        posts.append({
            "title": titles[i].strip(),
            "score": int(scores[i]),
            "num_comments": int(comment_counts[i]) if i < len(comment_counts) else 0,
            "permalink": permalinks[i],
            "published_at": published,
        })

    return posts


def _extract_keywords(text: str) -> list[str]:
    crypto_terms = {
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "defi",
        "nft", "altcoin", "memecoin", "web3", "crypto", "blockchain",
        "etf", "regulation", "india", "layer 2", "l2", "stablecoin",
        "airdrop", "yield", "trading", "scam", "wallet",
    }
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return sorted(words & crypto_terms)
