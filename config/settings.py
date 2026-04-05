# ─────────────────────────────────────────────
#  LeadForge AI — Central Configuration
# ─────────────────────────────────────────────

# ── Ollama ────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "qwen3:8b"   # ← change model here only

# ── Per-agent LLM settings ────────────────────
PLANNER_TEMPERATURE   = 0.2
QUERY_TEMPERATURE     = 0.3
EXTRACTOR_TEMPERATURE = 0.1
ENRICH_TEMPERATURE    = 0.1
REPORTER_TEMPERATURE  = 0.4

# ── Search ────────────────────────────────────
MAX_SEARCH_QUERIES    = 15   # max queries per pipeline run
MAX_URLS_PER_QUERY    = 5    # DuckDuckGo results per query
MAX_TOTAL_URLS        = 25   # cap on URLs passed to scraper
SEARCH_TIMEOUT_SEC    = 10   # per-query timeout

# ── Scraper ───────────────────────────────────
SCRAPER_PAGE_TIMEOUT_MS = 12000   # Playwright page load timeout (ms)
SCRAPER_HARD_TIMEOUT_SEC = 20     # asyncio.wait_for timeout (sec)
MAX_PAGE_TEXT_CHARS   = 3000      # truncate scraped text to this length

# ── Pipeline ─────────────────────────────────
ENRICH_BATCH_SIZE     = 5         # leads per enrichment LLM call

# ── App ───────────────────────────────────────
APP_USERNAME = "admin"
APP_PASSWORD = "admin"
