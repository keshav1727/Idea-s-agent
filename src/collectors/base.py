"""Base collector with strict filters: 90-day date, crypto-only, viral-only.

No sample/hardcoded fallback — if live fetch fails, returns empty with error message.
"""

from __future__ import annotations
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.schema import ContentItem

MAX_AGE_DAYS = 90

STRONG_CRYPTO_KEYWORDS = {
    "bitcoin", "btc", "ethereum", "eth", "solana", "cryptocurrency",
    "blockchain", "defi", "altcoin", "memecoin", "stablecoin",
    "binance", "coinbase", "nft", "web3",
    "dogecoin", "doge", "shiba", "cardano", "polygon",
    "uniswap", "aave", "staking", "tokenomics",
    "hodl", "satoshi",
}

WEAK_CRYPTO_KEYWORDS = {
    "crypto", "token", "mining", "wallet", "exchange",
    "yield", "airdrop", "whale", "pump", "dump",
    "dex", "dao", "halving", "ledger", "gas",
    "bull", "bear", "trading",
}

VIRAL_THRESHOLDS = {
    "youtube": {"views": 100_000},
    "reddit": {"score": 100},
    "twitter": {"likes": 50},
    "news": None,
    "social": None,
}


def _is_within_date_range(published_at: str) -> bool:
    if not published_at:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except (ValueError, TypeError):
        pass
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(published_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except Exception:
        pass
    return False


def _is_crypto_related(item: ContentItem) -> bool:
    text = f"{item.title} {item.description}".lower()
    if len(item.title.strip()) < 15:
        return False
    words = set(re.findall(r"[a-z0-9]+", text))
    if words & STRONG_CRYPTO_KEYWORDS:
        return True
    weak_hits = words & WEAK_CRYPTO_KEYWORDS
    if len(weak_hits) >= 2:
        return True
    phrases = ["bull run", "bear market", "smart contract", "gas fee",
               "rug pull", "play to earn", "layer 2", "on-chain"]
    for phrase in phrases:
        if phrase in text:
            return True
    return False


def _is_viral(item: ContentItem) -> bool:
    thresholds = VIRAL_THRESHOLDS.get(item.platform)
    if thresholds is None:
        return True
    raw = item.engagement_raw
    for metric, min_val in thresholds.items():
        if raw.get(metric, 0) >= min_val:
            return True
    return False


class BaseCollector(ABC):
    """All collectors inherit this. No hardcoded fallback — real data or nothing."""

    platform: str = ""

    @abstractmethod
    def fetch_live(self) -> list[ContentItem]:
        ...

    @abstractmethod
    def _parse_sample(self, raw: list[dict]) -> list[ContentItem]:
        ...

    def collect(self) -> list[ContentItem]:
        """Fetch live data, apply filters. If fetch fails, return empty with error."""
        try:
            items = self.fetch_live()
            if items:
                return self._apply_filters(items)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "forbidden" in error_msg.lower():
                print(f"  [{self.platform}] ACCESS DENIED — API key invalid or plan upgrade needed")
            elif "quota" in error_msg.lower() or "429" in error_msg:
                print(f"  [{self.platform}] API QUOTA EXHAUSTED — try again after quota resets")
            elif "api_key" in error_msg.lower() or "not set" in error_msg.lower():
                print(f"  [{self.platform}] NO API KEY — set it in .env file")
            else:
                print(f"  [{self.platform}] FETCH FAILED — {error_msg}")

        print(f"  [{self.platform}] 0 items (source unavailable)")
        return []

    def _apply_filters(self, items: list[ContentItem]) -> list[ContentItem]:
        total = len(items)
        items = [i for i in items if _is_within_date_range(i.published_at)]
        after_date = len(items)
        items = [i for i in items if _is_crypto_related(i)]
        after_crypto = len(items)
        items = [i for i in items if _is_viral(i)]
        after_viral = len(items)

        parts = []
        if total - after_date:
            parts.append(f"{total - after_date} old")
        if after_date - after_crypto:
            parts.append(f"{after_date - after_crypto} non-crypto")
        if after_crypto - after_viral:
            parts.append(f"{after_crypto - after_viral} low-engagement")
        filter_info = f" (dropped {', '.join(parts)})" if parts else ""

        print(f"  [{self.platform}] {after_viral} items{filter_info}")
        return items
