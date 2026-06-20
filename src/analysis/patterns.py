"""Pattern detection: hooks, topics, storytelling structures, trending narratives."""

from __future__ import annotations
import re
import math
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Any

from src.schema import ContentItem


@dataclass
class PatternReport:
    """Full output of the pattern analysis stage."""
    viral_hooks: list[dict[str, Any]]
    popular_topics: list[dict[str, Any]]
    storytelling_structures: list[dict[str, Any]]
    trending_narratives: list[dict[str, Any]]
    top_content: list[dict[str, Any]]

    def to_dict(self) -> dict:
        return asdict(self)


# ── Hook detection ──────────────────────────────────────────────────

HOOK_PATTERNS: list[tuple[str, str]] = [
    (r"\bhow\b.*\b(to|i|we)\b", "how-to"),
    (r"\d+\s*(ways?|tips?|reasons?|things?|steps?|secrets?|rules?|mistakes?)", "listicle"),
    (r"^(why|what if|did you know|the truth about)", "curiosity-gap"),
    (r"\b(nobody|no one|everyone|they don't)\b.*\b(talks?|knows?|wants?|sees?)\b", "curiosity-gap"),
    (r"\b(unpopular opinion|hot take|controversial)\b", "contrarian"),
    (r"\b(stop|don't|never|quit|forget)\b", "contrarian"),
    (r"\b(breaking|just in|exposed|leaked|proof)\b", "urgency"),
    (r"\b(made|earned|turned|worth)\b.*\$[\d,]+[kKmMbB]?", "transformation"),
    (r"\b(shocking|insane|crazy|unbelievable|mind.?blowing)\b", "power-word"),
    (r"\?$", "question"),
    (r"\b(vs\.?|versus|compared|better)\b", "comparison"),
    (r"\b(my|i|i'm|i've)\b.*\b(journey|story|experience|quit|left)\b", "personal-story"),
]


def detect_hooks(items: list[ContentItem]) -> list[dict[str, Any]]:
    """Categorize viral hooks found in titles/openers."""
    hooks_by_category: dict[str, list[dict]] = {}

    for item in items:
        text = item.title.lower()
        for pattern, category in HOOK_PATTERNS:
            if re.search(pattern, text):
                hooks_by_category.setdefault(category, []).append({
                    "text": item.title,
                    "platform": item.platform,
                    "engagement_score": item.engagement_score,
                })

    result = []
    for category, examples in sorted(hooks_by_category.items()):
        top = sorted(examples, key=lambda x: x["engagement_score"], reverse=True)[:3]
        result.append({
            "category": category,
            "count": len(examples),
            "examples": top,
        })
    return sorted(result, key=lambda x: x["count"], reverse=True)


# ── Topic extraction (TF-IDF-like) ─────────────────────────────────

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "that", "this",
    "these", "those", "it", "its", "my", "your", "his", "her", "our",
    "their", "what", "which", "who", "whom", "about", "up", "s", "t",
    "re", "ve", "d", "ll", "m", "don", "you", "i", "we", "they", "he",
    "she", "me", "him", "us", "them", "new", "one", "two", "first",
    "also", "get", "got", "go", "going", "make", "know", "see", "come",
}


def extract_topics(items: list[ContentItem]) -> list[dict[str, Any]]:
    """TF-IDF-style keyword extraction with engagement weighting."""
    doc_freq: Counter[str] = Counter()
    term_scores: Counter[str] = Counter()
    term_items: dict[str, list[str]] = {}
    n_docs = len(items)

    for item in items:
        text = f"{item.title} {item.description}".lower()
        words = set(re.findall(r"[a-z]{3,}", text)) - STOP_WORDS
        for word in words:
            doc_freq[word] += 1

    for item in items:
        text = f"{item.title} {item.description}".lower()
        words = re.findall(r"[a-z]{3,}", text)
        word_counts = Counter(w for w in words if w not in STOP_WORDS)
        for word, tf in word_counts.items():
            idf = math.log(n_docs / (1 + doc_freq[word]))
            score = tf * idf * (item.engagement_score / 50)  # weight by engagement
            term_scores[word] += score
            term_items.setdefault(word, []).append(item.title)

    topics = []
    for word, score in term_scores.most_common(20):
        topics.append({
            "topic": word,
            "relevance_score": round(score, 2),
            "appears_in": len(term_items[word]),
            "example_titles": term_items[word][:3],
        })
    return topics


# ── Storytelling structures ─────────────────────────────────────────

STRUCTURE_PATTERNS: list[tuple[str, str, str]] = [
    (r"(how|strategy|tutorial|step|guide|walkthrough)", "how-to / explainer",
     "Educational content breaking down a process or concept step by step"),
    (r"(made|earned|turned|journey|quit|went from|story)", "transformation / journey",
     "Personal narrative showing before → after or a life-changing decision"),
    (r"(prediction|will|going to|about to|could|next)", "prediction / thesis",
     "Forward-looking analysis making a bold claim about what comes next"),
    (r"(vs|versus|compared|better|winner|flip)", "comparison / debate",
     "Head-to-head analysis pitting two options against each other"),
    (r"(breaking|just|hacked|stolen|exposed|scam)", "news reaction / exposé",
     "Reacting to or investigating a breaking event or scandal"),
    (r"(why|reason|truth|real|actually|nobody)", "myth-busting / contrarian",
     "Challenging conventional wisdom or revealing hidden truths"),
    (r"(top|best|worst|\d+\s*(altcoins?|coins?|tokens?|projects?))", "listicle / ranking",
     "Curated list of items ranked or grouped by a shared theme"),
]


def classify_structures(items: list[ContentItem]) -> list[dict[str, Any]]:
    """Classify each content item into storytelling structures."""
    struct_map: dict[str, list[dict]] = {}

    for item in items:
        text = item.title.lower()
        matched = False
        for pattern, structure, description in STRUCTURE_PATTERNS:
            if re.search(pattern, text):
                struct_map.setdefault(structure, []).append({
                    "title": item.title,
                    "platform": item.platform,
                    "engagement_score": item.engagement_score,
                    "description": description,
                })
                matched = True
                break
        if not matched:
            struct_map.setdefault("general / opinion", []).append({
                "title": item.title,
                "platform": item.platform,
                "engagement_score": item.engagement_score,
                "description": "General commentary or opinion piece",
            })

    results = []
    for structure, examples in struct_map.items():
        top = sorted(examples, key=lambda x: x["engagement_score"], reverse=True)[:3]
        results.append({
            "structure": structure,
            "count": len(examples),
            "description": examples[0]["description"],
            "top_examples": [e["title"] for e in top],
        })
    return sorted(results, key=lambda x: x["count"], reverse=True)


# ── Trending narratives ─────────────────────────────────────────────

NARRATIVE_KEYWORDS: dict[str, list[str]] = {
    "Bitcoin ETF & Institutional Adoption": ["etf", "institutional", "blackrock", "inflow", "wall street"],
    "Memecoin Mania": ["memecoin", "meme", "degen", "100x", "pump"],
    "India Crypto Ecosystem": ["india", "indian", "tax", "regulation", "rupee"],
    "DeFi Renaissance": ["defi", "yield", "apy", "lending", "liquidity", "aave", "uniswap"],
    "Solana vs Ethereum": ["solana", "sol", "ethereum", "eth", "flippening", "layer"],
    "AI x Crypto Convergence": ["ai", "artificial intelligence", "machine learning", "agent"],
    "Security & Scams": ["hack", "scam", "stolen", "rug", "security", "wallet"],
    "Web3 Gaming & NFTs": ["gaming", "nft", "play", "metaverse", "game"],
    "Regulation & Compliance": ["regulation", "law", "bill", "compliance", "sec", "legal"],
    "RWA Tokenization": ["rwa", "tokenization", "real world", "treasury", "bond"],
}


def detect_narratives(items: list[ContentItem]) -> list[dict[str, Any]]:
    """Aggregate recurring narratives from the highest-engagement content."""
    narrative_scores: dict[str, float] = {}
    narrative_examples: dict[str, list[str]] = {}

    for item in items:
        text = f"{item.title} {item.description}".lower()
        for narrative, keywords in NARRATIVE_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                score = hits * item.engagement_score
                narrative_scores[narrative] = narrative_scores.get(narrative, 0) + score
                narrative_examples.setdefault(narrative, []).append(item.title)

    results = []
    for narrative, score in sorted(narrative_scores.items(), key=lambda x: x[1], reverse=True):
        results.append({
            "narrative": narrative,
            "strength_score": round(score, 1),
            "content_count": len(narrative_examples[narrative]),
            "examples": narrative_examples[narrative][:3],
        })
    return results


# ── Main analysis entry point ───────────────────────────────────────

def analyze(items: list[ContentItem]) -> PatternReport:
    """Run full pattern analysis on collected content items."""
    sorted_items = sorted(items, key=lambda x: x.engagement_score, reverse=True)

    top_content = [
        {
            "title": item.title,
            "platform": item.platform,
            "engagement_score": item.engagement_score,
            "url": item.url,
        }
        for item in sorted_items[:15]
    ]

    return PatternReport(
        viral_hooks=detect_hooks(sorted_items),
        popular_topics=extract_topics(sorted_items),
        storytelling_structures=classify_structures(sorted_items),
        trending_narratives=detect_narratives(sorted_items),
        top_content=top_content,
    )
