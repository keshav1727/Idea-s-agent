"""Content idea generation using LLM — separate calls for better quality."""

from __future__ import annotations
import json
import os
from typing import Any

from src.analysis.patterns import PatternReport
from src.generator.llm_client import LLMClient, OllamaClient, OpenAIClient


SYSTEM_PROMPT = """You are a viral crypto content strategist for India's largest crypto education platform with 400K+ community members.
Your job: turn trending crypto data into content ideas that will go VIRAL.
Rules: emotional hooks with specific numbers, curiosity gaps, bold claims, relatable stories.
Return ONLY valid JSON. No markdown, no explanation. Start with {{ and end with }}."""


def _build_context(patterns: PatternReport) -> str:
    """Build a concise context string from patterns."""
    lines = ["Here is REAL trending crypto data scraped today:\n"]

    lines.append("TOP VIRAL CONTENT:")
    for t in patterns.top_content[:8]:
        lines.append(f"- [{t['platform']}] \"{t['title'][:100]}\" (score: {t['engagement_score']})")

    lines.append("\nTRENDING NARRATIVES:")
    for n in patterns.trending_narratives[:6]:
        lines.append(f"- {n['narrative']} ({n['content_count']} items, strength: {n['strength_score']})")

    lines.append("\nVIRAL HOOK TYPES:")
    for h in patterns.viral_hooks[:6]:
        lines.append(f"- {h['category']} ({h['count']} instances)")

    lines.append("\nHOT KEYWORDS:")
    kws = [t['topic'] for t in patterns.popular_topics[:10]]
    lines.append(", ".join(kws))

    return "\n".join(lines)


REEL_PROMPT = """{context}

---

Generate exactly 5 viral Instagram Reel ideas for a crypto education channel.
Each reel is 30-60 seconds, visual-first, designed for maximum saves and shares.

Return a JSON array of 5 objects. Each object MUST have these fields:
- "hook": string, the opening line shown on screen in first 2 seconds (make it shocking, specific, use numbers)
- "topic": string, what the reel teaches or reveals
- "angle": string, 2-3 sentences describing the storyline and visual approach
- "why_it_works": string, which viral pattern it uses
- "script_outline": array of 5-6 strings, beat-by-beat content flow

Example format:
[
  {{
    "hook": "This $500 investment turned into $2M in 18 months",
    "topic": "Memecoin trading rules that actually work",
    "angle": "Follow a real trader's journey. Open with portfolio screenshot, then reveal the 3 rules they never broke. End with CTA to follow.",
    "why_it_works": "Transformation hook + specific numbers = instant curiosity and FOMO",
    "script_outline": ["Open with shocking portfolio value", "Flashback to starting amount", "Rule 1 reveal", "Rule 2 reveal", "Rule 3 reveal", "CTA: Follow for more"]
  }}
]

Use the REAL trending data above. Make each idea DIFFERENT — different topics, different hook styles.
Return ONLY the JSON array."""


VIDEO_PROMPT = """{context}

---

Generate exactly 3 YouTube video ideas for a crypto education channel (10-20 min deep dives).
These should be the kind of videos that get millions of views — data-heavy, well-researched, bold claims.

Return a JSON array of 3 objects. Each MUST have:
- "hook": string, the thumbnail text / title (under 60 chars, curiosity-driven)
- "topic": string, the subject
- "angle": string, 2-3 sentences on the narrative approach
- "why_it_works": string, which viral pattern it leverages
- "script_outline": array of 6-8 strings, section-by-section breakdown

Example:
[
  {{
    "hook": "I analyzed 1000 wallets that made 100x — here are the 5 patterns",
    "topic": "On-chain analysis of winning crypto strategies",
    "angle": "Data-driven deep dive using blockchain data. Show real wallets, real numbers. No opinions, just data. Viewers trust data over influencer takes.",
    "why_it_works": "Listicle + data authority + large sample size signals serious research",
    "script_outline": ["Cold open: show most profitable wallet", "Methodology explanation", "Pattern 1 with examples", "Pattern 2 with examples", "Pattern 3", "Pattern 4", "Pattern 5", "Actionable takeaways"]
  }}
]

Make each video COMPLETELY different — different topics, different formats.
Return ONLY the JSON array."""


THREAD_PROMPT = """{context}

---

Write exactly 3 complete Twitter/X threads for a crypto education account. Each thread has 7 tweets.

IMPORTANT: Write the COMPLETE text of every tweet, not summaries. Each tweet under 280 characters.

Return a JSON array of 3 objects. Each MUST have:
- "hook": string, full text of Tweet 1 (the scroll-stopper, include emojis)
- "topic": string, the subject
- "angle": string, 2-3 sentences on the thread's narrative
- "why_it_works": string, which viral pattern it uses
- "tweets": array of 7 strings, the FULL TEXT of each tweet posted

Example of one thread object:
{{
  "hook": "Bitcoin just broke $120K and nobody is talking about it.\\n\\nIn 2021, $69K was front page news everywhere.\\nThis time? Silence.\\n\\nThat's how you know we're still early. Thread 🧵",
  "topic": "Why this Bitcoin rally is different",
  "angle": "Comparison thread: 2021 vs 2026 using data points. Each tweet covers one metric proving this cycle is fundamentally different.",
  "why_it_works": "Curiosity gap + contrarian take drives engagement. Both bulls and skeptics engage.",
  "tweets": [
    "Bitcoin just broke $120K and nobody is talking about it.\\n\\nIn 2021, $69K was front page news.\\nThis time? Silence.\\n\\nThat's how you know we're still early. Thread 🧵",
    "1/ In 2021, retail drove the rally.\\nIn 2026, it's institutions.\\n\\nBlackRock's ETF alone has $50B+ in inflows.\\nThat's more than entire crypto market cap in 2017.",
    "2/ Google searches for 'Bitcoin' are at 40% of 2021 peak.\\nBut price is 2x higher.\\n\\nSmart money buying while retail sleeps.\\nWhen normies wake up, we go parabolic.",
    "3/ In 2021, leverage was insane. 100x positions everywhere.\\nIn 2026, funding rates are neutral.\\n\\nThis rally has a REAL foundation, not a leverage casino.",
    "4/ Developer activity is 3x higher than 2021.\\nMore builders = more real products = more real users.\\n\\nThis isn't speculation. It's adoption.",
    "5/ The macro is different.\\n2021: Stimulus checks into Doge.\\n2026: Rate cuts, institutional allocations, sovereign funds.\\n\\nCompletely different game.",
    "6/ What should you do?\\n- DCA, don't FOMO\\n- Focus on fundamentals\\n- Take profits on the way up\\n- Never invest more than you can lose\\n\\nThe opportunity is here.\\nFollow for more crypto alpha 🔥"
  ]
}}

Make 3 threads on DIFFERENT topics. Write FULL tweet text for ALL 7 tweets in each thread.
Return ONLY the JSON array."""


HOOKS_PROMPT = """{context}

---

Based on the viral content data above, generate:
1. "viral_hooks": array of 15 reusable hook TEMPLATES (use [brackets] for fillable slots)
2. "trending_web3_topics": array of 10 trending topics with fields: "topic" (string), "engagement_rank" (1-10), "trend_direction" ("surging"/"hot"/"rising"/"emerging"/"stable"), "why" (one sentence)

Return a JSON object with these 2 keys. Example:
{{
  "viral_hooks": [
    "This $[small amount] turned into $[large amount] in [time period]",
    "[Number] [things] about [topic] that nobody talks about"
  ],
  "trending_web3_topics": [
    {{"topic": "Bitcoin ETF Flows", "engagement_rank": 1, "trend_direction": "surging", "why": "Record ETF inflows"}}
  ]
}}

Return ONLY the JSON object."""


def get_llm_client() -> tuple[LLMClient, str]:
    """Select the best available LLM backend."""
    backend = os.getenv("LLM_BACKEND", "ollama").lower()

    if backend == "openai" and os.getenv("OPENAI_API_KEY"):
        return OpenAIClient(), "openai"

    if backend == "ollama":
        try:
            import ollama
            result = ollama.list()
            if hasattr(result, "models"):
                available = result.models
            elif isinstance(result, dict):
                available = result.get("models", [])
            else:
                available = []
            if available:
                target = os.getenv("OLLAMA_MODEL", "llama3")
                def get_name(m):
                    return m.model if hasattr(m, "model") else (m.get("name", "") if isinstance(m, dict) else str(m))
                names = [get_name(m).split(":")[0] for m in available]
                if target in names:
                    return OllamaClient(target), f"ollama ({target})"
                return OllamaClient(get_name(available[0])), f"ollama ({get_name(available[0])})"
        except Exception:
            pass

    if os.getenv("OPENAI_API_KEY"):
        return OpenAIClient(), "openai"

    raise RuntimeError(
        "No LLM backend available. Install Ollama and run 'ollama pull llama3', "
        "or set OPENAI_API_KEY in .env"
    )


def generate_ideas(patterns: PatternReport) -> dict[str, Any]:
    """Generate content ideas with separate LLM calls for better quality."""
    client, backend_name = get_llm_client()
    print(f"  [generator] Using LLM backend: {backend_name}")

    context = _build_context(patterns)
    ideas: dict[str, Any] = {}

    # Generate each category separately for higher quality
    steps = [
        ("Instagram Reels", REEL_PROMPT, "instagram_reels", list),
        ("YouTube Videos", VIDEO_PROMPT, "youtube_videos", list),
        ("Twitter Threads", THREAD_PROMPT, "twitter_threads", list),
        ("Hooks & Trends", HOOKS_PROMPT, "hooks_and_trends", dict),
    ]

    for label, prompt_template, key, expected_type in steps:
        print(f"  [generator] Generating {label}...")
        prompt = prompt_template.format(context=context)
        result = _call_with_retry(client, prompt, expected_type)
        if result is not None:
            if key == "hooks_and_trends":
                ideas["viral_hooks"] = result.get("viral_hooks", [])
                ideas["trending_web3_topics"] = result.get("trending_web3_topics", [])
            else:
                ideas[key] = result
            print(f"  [generator] {label}: OK")
        else:
            print(f"  [generator] {label}: FAILED")
            if key == "hooks_and_trends":
                ideas.setdefault("viral_hooks", [])
                ideas.setdefault("trending_web3_topics", [])
            else:
                ideas[key] = []

    total = len(ideas.get("instagram_reels", [])) + len(ideas.get("youtube_videos", [])) + len(ideas.get("twitter_threads", []))
    print(f"  [generator] Total: {total} content ideas generated")
    return ideas


def _call_with_retry(client: LLMClient, prompt: str, expected_type: type, retries: int = 2) -> Any:
    """Call LLM and parse JSON, retry on failure."""
    for attempt in range(retries + 1):
        try:
            raw = client.generate(prompt, system=SYSTEM_PROMPT)
            cleaned = _extract_json(raw, expected_type)
            parsed = json.loads(cleaned)
            if not isinstance(parsed, expected_type):
                raise ValueError(f"Expected {expected_type.__name__}, got {type(parsed).__name__}")
            return parsed
        except Exception as e:
            if attempt < retries:
                print(f"  [generator] Parse failed ({e}), retrying...")
            else:
                print(f"  [generator] All attempts failed: {e}")
    return None


def _extract_json(text: str, expected_type: type) -> str:
    """Extract JSON from LLM response."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") or part.startswith("["):
                text = part
                break

    if expected_type == list:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return text[start:end + 1]
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end + 1]
    return text
