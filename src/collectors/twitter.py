"""Twitter/X collector — uses Twitter API v2 recent search with bearer token."""

from __future__ import annotations
import os
import re
from datetime import datetime, timedelta, timezone

import requests

from src.schema import ContentItem, normalize_engagement
from src.collectors.base import BaseCollector

SEARCH_QUERIES = [
    "crypto lang:en -is:retweet -is:reply",
    "bitcoin lang:en -is:retweet -is:reply",
    "ethereum OR solana lang:en -is:retweet -is:reply",
    "memecoin lang:en -is:retweet -is:reply",
    "defi OR web3 lang:en -is:retweet -is:reply",
    "altcoin lang:en -is:retweet -is:reply",
]


class TwitterCollector(BaseCollector):
    platform = "twitter"

    def fetch_live(self) -> list[ContentItem]:
        bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
        if not bearer:
            raise ValueError("TWITTER_BEARER_TOKEN not set")

        headers = {"Authorization": f"Bearer {bearer}"}
        items: list[ContentItem] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        start_time = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        for query in SEARCH_QUERIES:
            try:
                resp = requests.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params={
                        "query": query,
                        "max_results": 10,
                        "tweet.fields": "public_metrics,created_at,author_id",
                        "expansions": "author_id",
                        "user.fields": "username",
                        "start_time": start_time,
                        "sort_order": "relevancy",
                    },
                    timeout=15,
                )

                if resp.status_code in (401, 403):
                    raise ValueError(f"Twitter API returned {resp.status_code} — upgrade to Basic plan ($100/mo) for search access")
                if resp.status_code == 429:
                    print(f"    [twitter] Rate limited, using {len(items)} tweets found so far")
                    break
                if resp.status_code != 200:
                    continue

                data = resp.json()
                users = {}
                for user in data.get("includes", {}).get("users", []):
                    users[user["id"]] = user.get("username", "")

                for tweet in data.get("data", []):
                    pm = tweet.get("public_metrics", {})
                    username = users.get(tweet.get("author_id", ""), "")
                    tweet_id = tweet.get("id", "")

                    metrics = {
                        "likes": pm.get("like_count", 0),
                        "retweets": pm.get("retweet_count", 0),
                        "replies": pm.get("reply_count", 0),
                        "views": pm.get("impression_count", 0),
                    }

                    text = tweet.get("text", "")
                    items.append(ContentItem(
                        platform="twitter",
                        title=text[:200],
                        url=f"https://x.com/{username}/status/{tweet_id}" if username else f"https://x.com/i/status/{tweet_id}",
                        engagement_raw=metrics,
                        engagement_score=normalize_engagement("twitter", metrics),
                        published_at=tweet.get("created_at", ""),
                        source_keywords=_extract_keywords(text),
                        description=text,
                    ))

            except requests.RequestException as e:
                print(f"    [twitter] Request failed: {e}")
                continue

        seen: set[str] = set()
        unique: list[ContentItem] = []
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                unique.append(item)

        if not unique:
            raise ValueError("Twitter API returned no results")
        return unique

    def _parse_sample(self, raw: list[dict]) -> list[ContentItem]:
        return []


def _extract_keywords(text: str) -> list[str]:
    crypto_terms = {
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "defi",
        "nft", "altcoin", "memecoin", "web3", "crypto", "blockchain",
        "etf", "regulation", "india", "layer 2", "l2", "stablecoin",
        "airdrop", "yield", "trading",
    }
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return sorted(words & crypto_terms)
