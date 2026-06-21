"""YouTube Data API v3 collector."""

from __future__ import annotations
import os
import re
from datetime import datetime, timedelta, timezone

from src.schema import ContentItem, normalize_engagement
from src.collectors.base import BaseCollector, MAX_AGE_DAYS

SEARCH_QUERIES = [
    "bitcoin explained for beginners",
    "how blockchain works",
    "what is defi explained",
    "crypto knowledge you need",
    "ethereum vs solana explained",
    "why bitcoin matters",
    "web3 explained simply",
    "crypto investing mistakes",
]


class YouTubeCollector(BaseCollector):
    platform = "youtube"

    def fetch_live(self) -> list[ContentItem]:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not set")

        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=api_key)
        video_ids: list[str] = []
        cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")

        for query in SEARCH_QUERIES:
            try:
                resp = youtube.search().list(
                    q=query, part="id", type="video",
                    order="relevance", maxResults=10,
                    publishedAfter=cutoff,
                    videoDuration="medium",
                ).execute()
                video_ids.extend(
                    item["id"]["videoId"]
                    for item in resp.get("items", [])
                    if item["id"].get("videoId")
                )
            except Exception as e:
                if "quota" in str(e).lower() or "429" in str(e):
                    print(f"    [youtube] API quota hit, using {len(video_ids)} videos found so far")
                    break
                raise

        video_ids = list(dict.fromkeys(video_ids))[:60]

        items: list[ContentItem] = []
        for i in range(0, len(video_ids), 50):
            batch = ",".join(video_ids[i:i + 50])
            resp = youtube.videos().list(
                id=batch, part="snippet,statistics",
            ).execute()
            for v in resp.get("items", []):
                stats = v["statistics"]
                snippet = v["snippet"]
                metrics = {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                }
                items.append(ContentItem(
                    platform="youtube",
                    title=snippet["title"],
                    url=f"https://youtube.com/watch?v={v['id']}",
                    engagement_raw=metrics,
                    engagement_score=normalize_engagement("youtube", metrics),
                    published_at=snippet["publishedAt"],
                    source_keywords=_extract_keywords(snippet["title"]),
                    description=snippet.get("description", "")[:500],
                ))
        return items

    def _parse_sample(self, raw: list[dict]) -> list[ContentItem]:
        return []


def _extract_keywords(text: str) -> list[str]:
    """Pull crypto-relevant keywords from text."""
    crypto_terms = {
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "defi",
        "nft", "altcoin", "memecoin", "web3", "crypto", "blockchain",
        "etf", "regulation", "india", "layer 2", "l2", "stablecoin",
        "airdrop", "yield", "trading", "bullrun", "bull run", "bear",
    }
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return sorted(words & crypto_terms)
