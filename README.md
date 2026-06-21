# ViralCryptoIdeas

An AI-powered system that collects viral crypto content from multiple platforms, identifies engagement patterns, and generates original content ideas for Instagram Reels, YouTube videos, and Twitter threads.

> For a detailed technical walkthrough, see [REPORT.md](REPORT.md).

## How It Works

The system runs a 4-stage pipeline:

```
Stage 1: COLLECT          Stage 2: ANALYZE          Stage 3: GENERATE         Stage 4: OUTPUT
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐      ┌──────────────┐
│ YouTube API      │      │ Hook detection   │      │ LLM generates:   │      │ report.md    │
│ Reddit RSS       │─────>│ Topic extraction │─────>│  5 IG Reels      │─────>│ ideas.json   │
│ News RSS feeds   │      │ Narrative trends │      │  3 YT Videos     │      │ patterns.json│
│ Google News      │      │ Story structures │      │  3 Twitter threads│     │ collected.json│
└──────────────────┘      └──────────────────┘      └──────────────────┘      └──────────────┘
```

**Stage 1 — Collect:** Scrapes viral crypto content from YouTube (via Data API v3), Reddit (via RSS), crypto news sites (CoinDesk, Cointelegraph, Decrypt via RSS), and Google News. Every item passes through three filters: must be from the last 90 days, must be crypto-related (keyword matching with strong/weak keyword tiers), and must have viral-level engagement (YouTube: 100K+ views, Reddit: 100+ upvotes).

**Stage 2 — Analyze:** Runs pattern detection on the collected content — categorizes viral hooks (curiosity gaps, listicles, contrarian takes, transformation stories), extracts trending topics via TF-IDF weighted by engagement, classifies storytelling structures, and identifies recurring narratives.

**Stage 3 — Generate:** Feeds the pattern analysis into an LLM (Ollama with llama3, or OpenAI-compatible API). Makes separate LLM calls for each content type (Reels, Videos, Threads) to ensure quality. Each generated idea includes a hook, topic, angle/storyline, and script outline.

**Stage 4 — Output:** Renders a Markdown report and saves raw JSON files for programmatic access.

## Project Structure

```
├── main.py                     # CLI entrypoint — runs full pipeline
├── dashboard.py                # API server + serves React build
├── src/
│   ├── schema.py               # ContentItem dataclass + engagement normalization
│   ├── collectors/
│   │   ├── base.py             # Base collector with date/crypto/viral filters
│   │   ├── youtube.py          # YouTube Data API v3 collector
│   │   ├── reddit.py           # Reddit HTML scraper (real upvotes/comments)
│   │   ├── news.py             # Crypto news RSS (CoinDesk, Cointelegraph, Decrypt)
│   │   └── twitter.py          # Twitter API v2 (needs paid Basic plan)
│   ├── analysis/
│   │   └── patterns.py         # Hook detection, TF-IDF topics, narrative analysis
│   ├── generator/
│   │   ├── llm_client.py       # LLM interface (Ollama / OpenAI)
│   │   └── content_ideas.py    # Prompt engineering + idea generation
│   └── output/
│       └── renderer.py         # Markdown report renderer
├── frontend/                   # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx             # Main app with tab routing
│   │   ├── api.js              # API client functions
│   │   └── components/         # FetchedPage, GeneratedPage, IdeaSection, etc.
│   ├── vite.config.js
│   └── package.json
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

**YouTube Data API v3** (required for live YouTube data):
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project, enable "YouTube Data API v3", create an API key
3. Set `YOUTUBE_API_KEY=your_key` in `.env`
4. Free tier: 10,000 units/day (~60 search queries)

**Reddit, News, Google News** — no API keys needed. These use RSS feeds.

**Twitter/X** — requires a paid Basic plan ($100/month) for search. The system falls back to Google News for crypto social content when Twitter API is unavailable.

**LLM** — the system uses Ollama (free, local) by default:
```bash
# Install Ollama
brew install ollama      # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh   # Linux

# Pull a model
ollama pull llama3

# Ollama must be running when you generate ideas
ollama serve
```

Alternatively, set `LLM_BACKEND=openai` and `OPENAI_API_KEY=your_key` to use OpenAI or any compatible API.

### 3. Run

**CLI:**
```bash
python main.py
```

**Dashboard:**
```bash
cd frontend && npm install && npm run build && cd ..
python dashboard.py
```
Opens a web dashboard at `http://localhost:8050`. Fetched data auto-refreshes on page load. Each idea section (Reels, Videos, Threads, Hooks) has its own Generate button.

## Output

The pipeline generates these files:

| File | Description |
|------|-------------|
| `report.md` | Formatted Markdown report with all ideas, patterns, and hooks |
| `output/ideas.json` | Generated content ideas (5 Reels, 3 Videos, 3 Threads) |
| `output/patterns.json` | Detected patterns (hooks, topics, narratives, structures) |
| `output/collected.json` | Raw scraped content with engagement metrics |

## Content Filtering

Every scraped item passes three filters before entering the pipeline:

1. **Date filter** — only content from the last 90 days (configurable via `MAX_AGE_DAYS` in `base.py`)
2. **Crypto relevance filter** — two-tier keyword matching:
   - Strong keywords (bitcoin, ethereum, defi, etc.) — one match is enough
   - Weak keywords (crypto, trading, mining, etc.) — need 2+ matches
   - Titles under 15 characters are rejected (filters hashtag spam)
3. **Viral threshold filter** — platform-specific minimums:
   - YouTube: 100,000+ views
   - Reddit: 100+ upvotes
   - News/Social: no threshold (content from crypto-specific sources)

## Engagement Normalization

Different platforms have different engagement scales. The `normalize_engagement()` function in `schema.py` converts platform-specific metrics to a comparable 0–100 score using log-dampened, weighted formulas:

- **YouTube**: 40% views + 35% likes + 25% comments
- **Reddit**: 55% upvotes + 45% comments
- **Twitter**: 30% likes + 25% retweets + 20% replies + 25% views

## Dashboard

The web dashboard (`dashboard.py`) has two tabs:

- **Fetched Data** — shows all scraped content with real engagement metrics, filterable by platform
- **Generated Ideas** — shows AI-generated content ideas with hooks, topics, angles, and script outlines

The Generate button runs the full pipeline in a background thread and updates the UI when complete.

## Design Decisions

- **RSS-first data collection**: Reddit and news sources use RSS feeds instead of authenticated APIs. This means zero setup for 3 out of 4 data sources. YouTube is the only source requiring an API key.

- **Three-filter pipeline in base collector**: Date, crypto relevance, and viral threshold filters run at the base collector level (`base.py`). No collector can bypass them. This is a single enforcement point.

- **Separate LLM calls per content type**: Instead of one large prompt asking for all content types, the generator makes 4 separate LLM calls (Reels, Videos, Threads, Hooks). This produces higher quality output from smaller models like llama3 8B.

- **No hardcoded fallback**: If a source fails (API quota, auth denied, network error), it returns zero items and logs the reason. No fake/sample data is ever shown.

- **React + Tailwind frontend**: Vite + React for the dashboard, Tailwind CSS for styling. Built to `frontend/dist/` and served by the Python stdlib HTTP server — no Flask/FastAPI dependency.

## Limitations

- **Twitter/X requires paid API**: The free Twitter API tier doesn't include search. The system falls back to Google News for crypto social content.
- **YouTube API quota**: Free tier allows ~60 search queries/day (10,000 units). Quota resets at midnight Pacific time.
- **LLM quality depends on model**: llama3 8B produces decent ideas. Larger models (llama3.1 70B, GPT-4) produce significantly better output.
- **Reddit RSS lacks engagement data**: Reddit RSS feeds don't include upvote/comment counts. Posts are included based on recency and crypto relevance.
- **English-only**: Content collection and analysis is English-language focused.

## Tech Stack

- **Python 3.12** — core language
- **Ollama** — local LLM inference (free)
- **YouTube Data API v3** — video search and metadata
- **feedparser** — RSS feed parsing (Reddit, news, Google News)
- **scikit-learn** — TF-IDF topic extraction (used in pattern analysis)
- **python-dotenv** — environment variable management
# Idea-s-agent
