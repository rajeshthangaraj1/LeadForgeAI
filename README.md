# LeadForge AI

**AI-Powered B2B/B2C Lead Generation & Email Outreach Platform**

LeadForge AI is a fully local, multi-agent platform that searches the internet, scrapes business directories, extracts and enriches leads using a local LLM, and manages email campaigns — all from a modern web dashboard. No paid APIs required. No cloud. Everything runs on your machine.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Reflex (Python full-stack) |
| Database | SQLite (WAL mode) |
| Agent Orchestration | LangGraph StateGraph |
| LLM (local) | Ollama (`qwen3:8b` default) |
| Web Search | DuckDuckGo (`ddgs`) + Google Maps + Bing |
| Web Scraping | Playwright (headless Chromium) + BeautifulSoup |
| Email | Gmail SMTP (send) + Gmail IMAP (reply monitor) |
| Data Processing | Pandas |

---

## Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv leadforge_env
source leadforge_env/bin/activate        # Linux / Mac

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browser
playwright install chromium

# 4. Install Ollama  →  https://ollama.com
#    Then pull the model:
ollama pull qwen3:8b

# 5. Run the app
reflex run
```

App runs at `http://localhost:3000`

**Login:** `admin` / `admin`
*(Change in `config/settings.py` → `APP_USERNAME` / `APP_PASSWORD`)*

---

## Project Structure

```
LeadForgeAI/
│
├── rxconfig.py                        Reflex app config
├── requirements.txt
├── README.md
├── PRODUCT_OVERVIEW.md                Team-facing product document
├── leadforge.db                       SQLite database (auto-created)
│
├── leadforge_ui/                      Reflex frontend application
│   ├── leadforge_ui.py                App entry point — registers all pages
│   ├── pages/                         One file per route
│   │   ├── login.py                   / and /login
│   │   ├── register.py                /register
│   │   ├── dashboard.py               /dashboard
│   │   ├── leads.py                   /leads
│   │   ├── lead_generator.py          /lead-generator
│   │   ├── campaigns.py               /campaigns
│   │   ├── masters.py                 /masters
│   │   ├── analytics.py               /analytics
│   │   └── settings_page.py           /settings
│   ├── state/                         One rx.State per page
│   │   ├── auth.py                    AuthState — login, register, logout, auth guard
│   │   ├── dashboard_state.py
│   │   ├── leads_state.py
│   │   ├── lead_generator_state.py
│   │   ├── campaigns_state.py
│   │   ├── masters_state.py
│   │   ├── analytics_state.py
│   │   └── settings_state.py
│   ├── components/                    Shared UI components (sidebar, cards, tables)
│   └── styles/                        Theme and style constants
│
├── config/
│   └── settings.py                    Central config (model, limits, credentials)
│
├── database/
│   └── sqlite_db.py                   SQLite schema, seed data, all DB helpers
│
├── agents/
│   ├── planner_agent.py               LLM: refines target into strategy + ICP
│   ├── query_agent.py                 LLM: generates B2B/B2C-aware search queries
│   ├── search_agent.py                Multi-provider URL + lead collection
│   ├── scraper_agent.py               Playwright: Pass 1 (pages) + Pass 2 (/contact, /about)
│   ├── extractor_agent.py             LLM: extracts name/company/role/email/phone/linkedin
│   ├── cleaner_agent.py               Dedup, normalise, score leads 0-10
│   ├── enrich_agent.py                LLM: industry / segment / company size / B2B type
│   ├── db_agent.py                    Filters + saves leads to SQLite
│   ├── reporter_agent.py              LLM: executive summary + analytics
│   └── providers/
│       ├── duckduckgo_provider.py     Free, no key needed
│       ├── bing_provider.py           Free, Playwright on bing.com
│       ├── google_maps_provider.py    Free, returns phone + address directly
│       ├── brave_provider.py          Paid — Brave Search API
│       ├── serper_provider.py         Paid — Serper.dev (Google results)
│       └── serpapi_provider.py        Paid — SerpAPI (Google results)
│
├── graph/
│   └── agent_graph.py                 LangGraph StateGraph pipeline wiring
│
├── pipeline/
│   └── run_pipeline.py                Entry point: start (fresh) / rerun (append)
│
└── utils/
    ├── helpers.py                     Email/phone/LinkedIn cleaners, text utils
    ├── llm_utils.py                   Ollama call wrapper, <think> stripping, JSON extract
    └── email_utils.py                 Gmail SMTP send, IMAP reply fetch, template render
```

---

## Pipeline Flow

```
Select Product → reads Target Audience from DB
        ↓
PlannerAgent       LLM refines strategy, builds ICP (Ideal Customer Profile)
        ↓
QueryAgent         LLM generates 12 B2B/B2C-aware short search queries
        ↓
SearchAgent        Multi-track URL + lead collection:
  Track 1          DuckDuckGo → general web URLs
  Track 2          Country directories → direct scrape (per country + B2B/B2C)
  Track 3          Google Maps → structured leads (name, phone, address) direct
  Track 4+         Bing / Brave / Serper / SerpAPI (if enabled)
        ↓
ScraperAgent       Playwright Pass 1: main pages (1.5 s JS wait)
                   Playwright Pass 2: /contact + /about sub-pages
                   URL pre-filter: skips PDFs, images, forums before loading
                   1 automatic retry on timeout/error
        ↓
ExtractorAgent     LLM extracts: name, company, role, email, phone, linkedin
                   Google Maps leads injected directly (no LLM needed)
        ↓
CleanerAgent       Dedup by fingerprint, normalise phones/emails/LinkedIn
                   Scores each lead 0–10 (email+3, phone+2, company+2, ...)
        ↓
EnrichAgent        LLM adds: industry, segment, company size, B2B/B2C
                   Skips leads already complete (faster)
        ↓
DBAgent            Drops 0-contact leads (no email AND no phone)
                   Cross-run dedup: skips leads already in DB for this product
                   Saves new leads with quality score
        ↓
ReporterAgent      LLM executive summary + top companies/industries/locations
        ↓
Leads Dashboard
```

---

## Features

### Phase 1 — Lead Generation

| Feature | Detail |
|---|---|
| Multi-product support | One company → multiple products → separate lead runs |
| Start vs Re-run | Start clears leads; Re-run appends without duplicates |
| Google Maps scraping | Phone number + address extracted directly (no LLM needed) |
| 13-country directories | UAE, India, Saudi Arabia, USA, UK, Australia, Qatar, Kuwait, Bahrain, Oman, Singapore, Germany, Canada |
| 6 search providers | DDG (free), Bing (free), Maps (free), Brave / Serper / SerpAPI (paid, key in UI) |
| Lead quality scoring | Every lead scored 0–10 based on data completeness |
| Cross-run deduplication | Same email not saved twice for the same product |
| 0-contact lead filter | Leads with no email AND no phone are dropped before saving |
| URL pre-filter | PDFs, images, forum/tag/archive URLs skipped before Playwright |
| 2-pass scraping | Main pages + /contact + /about for phone hunting |
| Retry on failure | Each URL gets 1 automatic retry on timeout |
| Executive reporting | LLM-generated summary + analytics per run |

### Phase 2 — Email Outreach

| Feature | Detail |
|---|---|
| Gmail integration | App Password — no OAuth required |
| Email templates | Reusable templates with placeholders: `{name}`, `{company}`, `{role}`, `{industry}`, `{location}` |
| Email campaigns | Create campaign → select product + template → send to filtered leads |
| Message-ID tracking | Every sent email gets a unique Message-ID stored in DB |
| Reply monitoring | IMAP inbox scan matches replies by Message-ID + sender email fallback |
| Auto-reply detection | Filters out-of-office / vacation / auto-responders by headers + subject keywords |
| Reply sentiment | LLM classifies each real reply: Interested / Not Interested / Needs Info / Other |
| Campaign analytics | Sent, replied, auto-reply counts + reply rate % per campaign |

### Phase 3 — Lead Management

| Feature | Detail |
|---|---|
| Lead pipeline stages | New → Contacted → Replied → Qualified → Won / Lost |
| Notes per lead | Free-text context notes saved per lead |
| Stage filter | Filter dashboard by pipeline stage |
| Stage + score in table | Quality score and current stage visible in leads table |

---

## Search Providers

| Provider | Cost | Default | Notes |
|---|---|---|---|
| DuckDuckGo | Free | On | No key, general web |
| Google Maps | Free | On | Phone + address direct, no LLM needed |
| Bing | Free | Off | JS-rendered, Playwright |
| Brave Search | Paid | Off | Key from brave.com/search/api |
| Serper.dev | Paid | Off | Key from serper.dev — Google results |
| SerpAPI | Paid | Off | Key from serpapi.com — Google results |

---

## Database Tables

| Table | Purpose |
|---|---|
| `company_profile` | Company details |
| `products` | Multiple products per company |
| `target_audience` | Target config per product |
| `leads` | All leads (name, company, role, email, phone, linkedin, score, stage, notes) |
| `agent_runs` | Pipeline run history |
| `agent_logs` | Per-step logs for every agent |
| `country_sources` | Business directory URLs per country + B2B/B2C |
| `search_providers` | Provider config (enabled, api_key) |
| `gmail_config` | Gmail SMTP/IMAP credentials |
| `email_templates` | Reusable templates |
| `email_campaigns` | Campaigns (template + product + status) |
| `email_sends` | Per-email send record + Message-ID + reply tracking |

---

## Configuration (`config/settings.py`)

```python
OLLAMA_BASE_URL         = "http://localhost:11434"
OLLAMA_MODEL            = "qwen3:8b"       # change model here only

MAX_SEARCH_QUERIES      = 15               # queries per run
MAX_URLS_PER_QUERY      = 5                # results per DDG query
MAX_TOTAL_URLS          = 25               # cap on URLs to scrape

SCRAPER_PAGE_TIMEOUT_MS = 12000            # Playwright timeout (ms)
SCRAPER_HARD_TIMEOUT_SEC = 20              # asyncio.wait_for timeout (s)
MAX_PAGE_TEXT_CHARS     = 3000             # text extracted per page

ENRICH_BATCH_SIZE       = 5                # leads per enrichment LLM call

APP_USERNAME            = "admin"
APP_PASSWORD            = "admin"
```

**Changing the Ollama model** — edit `OLLAMA_MODEL` in `config/settings.py` only. Every agent uses this setting automatically.

Tested models: `qwen3:8b`, `mistral-small3.2`, `llama3.2`, `gemma3`, `phi4`, `deepseek-r1`

---

## GPU Acceleration (Ollama on DGX Spark / NVIDIA GPU)

If Ollama falls back to CPU, set environment variables in the service:

```bash
sudo systemctl edit ollama
```

Add:
```
[Service]
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="LD_LIBRARY_PATH=/usr/local/cuda/lib64"
```

Then restart: `sudo systemctl restart ollama`

---

## License

MIT — free to use, modify and distribute.
