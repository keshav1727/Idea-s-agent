# ViralCryptoIdeas — Documentation

## What is this?

An AI system that generates viral crypto content ideas for a creator team. It scrapes what's already going viral in crypto (YouTube videos with millions of views, trending Reddit posts, crypto news), figures out why that content works, and uses an AI model to generate new content ideas based on those real patterns.

## What does it produce?

- **5 Instagram Reel ideas** — 30-60 second format, with hook + script outline
- **3 YouTube Video ideas** — 10-20 minute deep dives, with section-by-section breakdown
- **3 Twitter Thread ideas** — 7 tweets each, full tweet text written out
- **15 reusable hook templates** — fill-in-the-blank hooks derived from viral content
- **10 trending crypto topics** — ranked by engagement strength

Every idea includes: a hook (attention-grabbing opener), topic, angle/storyline, why it works, and a beat-by-beat script outline.

## How does it work?

Three steps:

**Step 1 — Scrape viral crypto content**

Pulls high-engagement crypto content from 4 sources:
- YouTube (videos with 100K+ views via YouTube Data API)
- Reddit (top posts from r/CryptoCurrency, r/Bitcoin, r/ethereum with real upvotes/comments)
- Crypto news (CoinDesk, Cointelegraph, Decrypt via RSS)
- Twitter/X (real tweets with likes, RTs, replies via Twitter API)

Only content from the last 90 days. Only crypto-related. Only viral engagement levels.

**Step 2 — Analyze patterns**

Runs pattern detection on the scraped content:
- What types of hooks get the most engagement? (questions, listicles, contrarian takes, transformation stories, urgency, etc.)
- What crypto topics are trending? (Bitcoin ETF, memecoins, DeFi, India regulation, etc.)
- What storytelling structures work? (how-to, comparison, prediction, exposé, etc.)

**Step 3 — Generate ideas with AI**

Feeds the real patterns and real examples into an AI model (Meta's LLaMA 3 running locally via Ollama). The AI generates original content ideas based on what's actually trending — not generic ideas.

Each content type gets its own AI call (Reels, Videos, Threads, Hooks) so the output quality stays high.

## How to run it?

```bash
pip install -r requirements.txt     # Python dependencies
cd frontend && npm install && npm run build && cd ..   # Build React dashboard
python dashboard.py                 # Start dashboard at http://localhost:8050
```

Or CLI only:
```bash
python main.py                      # Outputs report.md + JSON files
```

## API Keys

| Service | What it does | Cost | How to get it |
|---------|-------------|------|---------------|
| **YouTube Data API** | Fetches real YouTube videos with views, likes, comments | Free (10K units/day) | [Google Cloud Console](https://console.cloud.google.com/) → create project → enable "YouTube Data API v3" → create API key |
| **Twitter/X API** | Fetches real tweets with likes, RTs, replies | $100/month (Basic plan) | [Twitter Developer Portal](https://developer.twitter.com/en/portal) → sign up → choose Basic plan → create app → generate Bearer Token |
| **Reddit** | Scrapes Reddit posts with real upvotes, comments | Free, no key needed | Works automatically |
| **News** | Fetches from CoinDesk, Cointelegraph, Decrypt | Free, no key needed | Works automatically |
| **Ollama** | Runs the AI model locally | Free | Install: `brew install ollama` → Pull model: `ollama pull llama3` → Start: `ollama serve` |

Add keys to `.env` file:
```
YOUTUBE_API_KEY=your-key
TWITTER_BEARER_TOKEN=your-token
```

**Minimum cost: ₹0** — YouTube free tier + Reddit + News + Ollama all free.
Twitter is optional ($100/month) — system works without it, just shows "Unavailable" for that source.
