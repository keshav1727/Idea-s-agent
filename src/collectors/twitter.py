"""Twitter/X collector — fetches tweets from top crypto accounts via API v2.

Pulls recent tweets from a curated list of the most influential crypto accounts
on X, then falls back to search if user timelines aren't available.
Requires a Twitter API Basic plan ($100/mo) bearer token.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta, timezone

import requests

from src.schema import ContentItem, normalize_engagement
from src.collectors.base import BaseCollector

CRYPTO_ACCOUNTS = [
    # ── Builders & founders (technical depth, protocol-level insight) ──
    "VitalikButerin",   # Ethereum co-founder — scaling, ZK proofs, AI x crypto
    "cz_binance",       # Binance founder — exchange trends, regulation
    "saylor",           # Michael Saylor — Bitcoin thesis, institutional adoption
    "aeyakovenko",      # Anatoly Yakovenko — Solana co-founder
    "StaniKulechov",    # Stani Kulechov — Aave founder, DeFi pioneer
    "cburniske",        # Chris Burniske — Placeholder VC, crypto valuations
    "ErikVoorhees",     # Erik Voorhees — ShapeShift founder, privacy & regulation

    # ── Researchers & deep analysts (data-driven, not hype) ──
    "CryptoHayes",      # Arthur Hayes — BitMEX co-founder, macro + trading mechanics
    "APompliano",       # Anthony Pompliano — accessible investor commentary
    "nic__carter",      # Nic Carter — Castle Island VC, on-chain analytics, mining
    "DefiIgnas",        # Ignas — DeFi research, yield strategies, protocol analysis
    "Route2FI",         # Route2FI — DeFi strategies, yield farming deep dives
    "MustStopMurad",    # Murad Mahmudov — memecoin supercycle thesis

    # ── Educators & long-form thinkers (quality content, not price pumps) ──
    "CryptoMichNL",     # Michaël van de Poppe — technical analysis, altcoin picks
    "Ashcryptoreal",    # Ash Crypto — forecasts, whale movements, macro trends
    "blknoiz06",        # Ansem — early Solana calls, AI agent thesis
    "coabordie",        # Cobie — market psychology, crypto commentary
    "lightcrypto",      # Light — trading psychology, market structure
    "inversebrah",      # Inversebrah — contrarian macro takes, DeFi commentary
    "RaoulGMI",         # Raoul Pal — macro economics x crypto thesis

    # ── On-chain & data accounts (whale tracking, fund flows) ──
    "lookonchain",      # Lookonchain — whale wallet tracking, on-chain data
    "EmberCN",          # EmberCN — on-chain fund flow analysis
]


class TwitterCollector(BaseCollector):
    platform = "twitter"

    def fetch_live(self) -> list[ContentItem]:
        bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
        if not bearer:
            raise ValueError("TWITTER_BEARER_TOKEN not set in .env")

        headers = {"Authorization": f"Bearer {bearer}"}
        items: list[ContentItem] = []

        # Step 1: Resolve usernames to IDs
        user_ids = self._resolve_users(headers)
        if not user_ids:
            raise ValueError("Twitter API — could not resolve any user accounts. Check your bearer token and API plan.")

        # Step 2: Fetch recent tweets from each account
        for username, user_id in user_ids.items():
            tweets = self._fetch_user_tweets(headers, user_id, username)
            items.extend(tweets)
            time.sleep(1)

        if not items:
            raise ValueError("No tweets fetched from any account")

        # Deduplicate
        seen: set[str] = set()
        unique: list[ContentItem] = []
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                unique.append(item)
        return unique

    def _resolve_users(self, headers: dict) -> dict[str, str]:
        """Batch lookup usernames → user IDs."""
        user_ids: dict[str, str] = {}

        # API allows up to 100 usernames per request
        usernames = ",".join(CRYPTO_ACCOUNTS)
        try:
            resp = requests.get(
                "https://api.twitter.com/2/users/by",
                headers=headers,
                params={"usernames": usernames, "user.fields": "public_metrics"},
                timeout=15,
            )
            if resp.status_code in (401, 403):
                raise ValueError(f"Twitter API {resp.status_code} — upgrade to Basic plan ($100/mo) for user timeline access")
            if resp.status_code == 429:
                raise ValueError("Twitter API rate limited")
            if resp.status_code != 200:
                raise ValueError(f"Twitter API error {resp.status_code}")

            for user in resp.json().get("data", []):
                user_ids[user["username"]] = user["id"]
            print(f"    [twitter] Resolved {len(user_ids)} accounts")

        except requests.RequestException as e:
            raise ValueError(f"Twitter API request failed: {e}")

        return user_ids

    def _fetch_user_tweets(self, headers: dict, user_id: str, username: str) -> list[ContentItem]:
        """Fetch recent non-reply, non-retweet tweets from one account."""
        items: list[ContentItem] = []
        try:
            resp = requests.get(
                f"https://api.twitter.com/2/users/{user_id}/tweets",
                headers=headers,
                params={
                    "max_results": 10,
                    "tweet.fields": "public_metrics,created_at",
                    "exclude": "retweets,replies",
                },
                timeout=15,
            )
            if resp.status_code == 429:
                print(f"    [twitter] Rate limited on @{username}, skipping")
                return []
            if resp.status_code != 200:
                return []

            for tweet in resp.json().get("data", []):
                pm = tweet.get("public_metrics", {})
                tweet_id = tweet.get("id", "")
                text = tweet.get("text", "")

                metrics = {
                    "likes": pm.get("like_count", 0),
                    "retweets": pm.get("retweet_count", 0),
                    "replies": pm.get("reply_count", 0),
                    "views": pm.get("impression_count", 0),
                }

                items.append(ContentItem(
                    platform="twitter",
                    title=f"@{username}: {text[:180]}",
                    url=f"https://x.com/{username}/status/{tweet_id}",
                    engagement_raw=metrics,
                    engagement_score=normalize_engagement("twitter", metrics),
                    published_at=tweet.get("created_at", ""),
                    source_keywords=_extract_keywords(text),
                    description=text,
                ))

        except requests.RequestException:
            pass

        return items

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
