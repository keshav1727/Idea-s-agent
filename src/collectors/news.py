"""Crypto news RSS collector — CoinDesk, Cointelegraph, Decrypt. No API key needed."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from src.schema import ContentItem, normalize_engagement
from src.collectors.base import BaseCollector, MAX_AGE_DAYS

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]


class NewsCollector(BaseCollector):
    platform = "news"

    def fetch_live(self) -> list[ContentItem]:
        import feedparser

        items: list[ContentItem] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                summary = entry.get("summary", entry.get("description", ""))
                summary = re.sub(r"<[^>]+>", "", summary)[:500]
                published = entry.get("published", entry.get("updated", ""))
                try:
                    pub_dt = parsedate_to_datetime(published)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
                items.append(ContentItem(
                    platform="news",
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    engagement_raw={},
                    engagement_score=normalize_engagement("news", {}),
                    published_at=published,
                    source_keywords=_extract_keywords(entry.get("title", "")),
                    description=summary,
                ))
        return items

    def _parse_sample(self, raw: list[dict]) -> list[ContentItem]:
        return []


def _extract_keywords(text: str) -> list[str]:
    crypto_terms = {
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "defi",
        "nft", "altcoin", "memecoin", "web3", "crypto", "blockchain",
        "etf", "regulation", "india", "stablecoin", "airdrop", "rwa",
    }
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return sorted(words & crypto_terms)
