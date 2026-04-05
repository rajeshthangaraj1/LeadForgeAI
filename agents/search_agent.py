"""
Search Agent — multi-provider URL + lead collection.

Track 1  DuckDuckGo        free, always available
Track 2  Country directories  free, direct scrape URLs from DB
Track 3  Google Maps          free, returns structured leads directly
Track 4  Bing scraping        free, supports site: and filetype:pdf
Track 5+ Paid providers       Brave / Serper / SerpAPI — enabled via DB when API key added
"""
import time
import concurrent.futures
from database.sqlite_db import (
    log_agent_step,
    get_target_audience,
    get_active_directory_urls,
    get_enabled_search_providers,
)
from config.settings import MAX_URLS_PER_QUERY, MAX_TOTAL_URLS, SEARCH_TIMEOUT_SEC

SKIP_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "tiktok.com",
    "google.com", "bing.com", "yahoo.com", "wikipedia.org", "reddit.com",
}


def _should_skip(url: str) -> bool:
    return any(d in url for d in SKIP_DOMAINS)


def _run_text_search(provider_name: str, query: str, api_key: str = "") -> list[str]:
    """Dispatch a single query to the correct provider and return URLs."""
    try:
        if provider_name == "duckduckgo":
            from agents.providers.duckduckgo_provider import search
            return search(query, MAX_URLS_PER_QUERY)

        elif provider_name == "bing_scrape":
            from agents.providers.bing_provider import search
            return search(query, MAX_URLS_PER_QUERY)

        elif provider_name == "brave":
            from agents.providers.brave_provider import search
            return search(query, api_key, MAX_URLS_PER_QUERY)

        elif provider_name == "serper":
            from agents.providers.serper_provider import search
            return search(query, api_key, MAX_URLS_PER_QUERY)

        elif provider_name == "serpapi":
            from agents.providers.serpapi_provider import search
            return search(query, api_key, MAX_URLS_PER_QUERY)

    except Exception:
        pass
    return []


def run_search_agent(state: dict) -> dict:
    run_id     = state.get("run_id", 0)
    queries    = state.get("queries", [])
    product_id = state.get("product_id")

    target        = get_target_audience(product_id) if product_id else None
    country       = (target.get("country", "")       or "").strip() if target else ""
    business_type = (target.get("business_type", "B2B") or "B2B").strip() if target else "B2B"

    providers     = get_enabled_search_providers()
    provider_names = [p["name"] for p in providers]
    log_agent_step(run_id, "SearchAgent",
                   f"Enabled providers: {provider_names}")

    all_urls:     list[str] = []
    maps_leads:   list[dict] = []

    # ── Track 2: Country directory URLs (direct, no search) ───────────────────
    if country:
        dir_urls = get_active_directory_urls(country, business_type)
        log_agent_step(run_id, "SearchAgent",
                       f"Track 2 — {len(dir_urls)} directory URLs for {country} ({business_type})")
        all_urls.extend(dir_urls)
    else:
        log_agent_step(run_id, "SearchAgent",
                       "Track 2 — no country set, skipping directories.", "WARNING")

    # ── Track 3: Google Maps — returns structured leads directly ──────────────
    if "google_maps" in provider_names and queries:
        from agents.providers.google_maps_provider import scrape_maps_leads
        # Use first 8 queries for Maps — each returns ~8 businesses = ~64 leads
        maps_queries = queries[:8]
        log_agent_step(run_id, "SearchAgent",
                       f"Track 3 (Google Maps) — scraping {len(maps_queries)} queries...")
        for q in maps_queries:
            log_agent_step(run_id, "SearchAgent", f"  [Maps] {q}")
            try:
                leads = scrape_maps_leads(q, max_results=10)
                maps_leads.extend(leads)
                log_agent_step(run_id, "SearchAgent",
                               f"  [Maps] Found {len(leads)} businesses for: {q}")
            except Exception as e:
                log_agent_step(run_id, "SearchAgent",
                               f"  [Maps] Error: {e}", "WARNING")
        log_agent_step(run_id, "SearchAgent",
                       f"Track 3 done — {len(maps_leads)} Google Maps leads collected.")

    # ── Tracks 1, 4, 5+: Text search providers (DDG, Bing, paid) ─────────────
    text_providers = [p for p in providers if p["name"] not in ("google_maps",)]

    # If a paid provider is active, skip DuckDuckGo — paid providers already
    # cover the same queries with better quality (and support site:linkedin)
    _paid = {"serper", "brave", "serpapi"}
    if any(p["name"] in _paid for p in text_providers):
        before = len(text_providers)
        text_providers = [p for p in text_providers if p["name"] != "duckduckgo"]
        if len(text_providers) < before:
            log_agent_step(run_id, "SearchAgent",
                           "DuckDuckGo skipped — paid provider active (higher quality results).")

    if text_providers and queries:
        log_agent_step(run_id, "SearchAgent",
                       f"Running {len(queries)} queries across "
                       f"{len(text_providers)} text provider(s)...")
        for query in queries:
            for prov in text_providers:
                pname   = prov["name"]
                api_key = prov.get("api_key", "")
                log_agent_step(run_id, "SearchAgent",
                               f"  [{pname}] {query}")
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        future = ex.submit(_run_text_search, pname, query, api_key)
                        urls   = future.result(timeout=SEARCH_TIMEOUT_SEC)
                    filtered = [u for u in urls if not _should_skip(u)]
                    all_urls.extend(filtered)
                    log_agent_step(run_id, "SearchAgent",
                                   f"  [{pname}] → {len(filtered)} URLs")
                except concurrent.futures.TimeoutError:
                    log_agent_step(run_id, "SearchAgent",
                                   f"  [{pname}] TIMEOUT on: {query}", "WARNING")
                except Exception as e:
                    log_agent_step(run_id, "SearchAgent",
                                   f"  [{pname}] Error: {e}", "WARNING")
            time.sleep(1)  # polite delay between queries

    # ── Deduplicate URLs ──────────────────────────────────────────────────────
    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    unique_urls = unique_urls[:MAX_TOTAL_URLS]

    log_agent_step(run_id, "SearchAgent",
                   f"Total — {len(unique_urls)} URLs for scraping + "
                   f"{len(maps_leads)} Google Maps leads (direct, skip scraping)")

    state["urls"]       = unique_urls
    state["maps_leads"] = maps_leads   # injected straight into pipeline, bypasses scraper
    return state
