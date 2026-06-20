"""Unified content schema and engagement normalization."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ContentItem:
    """Platform-agnostic viral content item."""
    platform: str
    title: str
    url: str
    engagement_raw: dict[str, int]
    engagement_score: float  # 0–100 normalized
    published_at: str
    source_keywords: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_engagement(platform: str, metrics: dict[str, int]) -> float:
    """Scale platform-specific metrics to a comparable 0–100 score.

    Each platform has different engagement magnitudes, so we use
    platform-specific weighted formulas with log-dampened scaling.
    """
    import math

    def log_scale(value: int, ceiling: float) -> float:
        if value <= 0:
            return 0.0
        return min(100.0, (math.log10(value + 1) / math.log10(ceiling + 1)) * 100)

    if platform == "youtube":
        views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        view_score = log_scale(views, 10_000_000)
        like_score = log_scale(likes, 500_000)
        comment_score = log_scale(comments, 50_000)
        return round(view_score * 0.4 + like_score * 0.35 + comment_score * 0.25, 1)

    elif platform == "reddit":
        score = metrics.get("score", 0)
        comments = metrics.get("num_comments", 0)
        score_val = log_scale(score, 50_000)
        comment_val = log_scale(comments, 10_000)
        return round(score_val * 0.55 + comment_val * 0.45, 1)

    elif platform == "twitter":
        likes = metrics.get("likes", 0)
        retweets = metrics.get("retweets", 0)
        replies = metrics.get("replies", 0)
        views = metrics.get("views", 0)
        like_score = log_scale(likes, 200_000)
        rt_score = log_scale(retweets, 100_000)
        reply_score = log_scale(replies, 20_000)
        view_score = log_scale(views, 10_000_000)
        return round(like_score * 0.3 + rt_score * 0.25 + reply_score * 0.2 + view_score * 0.25, 1)

    elif platform == "news":
        # News items don't have engagement metrics; rank by recency proxy
        return 50.0

    return 50.0
