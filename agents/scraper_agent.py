"""
Scraper Agent
Pass 1 — scrape original URLs with JS wait for rendering.
Pass 2 — for each successful page, also try /contact and /about sub-pages
          to find phone numbers and emails that are hidden on main pages.
"""
import asyncio
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from database.sqlite_db import log_agent_step
from utils.helpers import truncate_text
from config.settings import (
    SCRAPER_PAGE_TIMEOUT_MS, SCRAPER_HARD_TIMEOUT_SEC, MAX_PAGE_TEXT_CHARS
)

SKIP_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "tiktok.com",
    "google.com", "bing.com", "yahoo.com",
    "wikipedia.org", "reddit.com",
}

# File extensions that are never useful to scrape for leads
_SKIP_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".mp4", ".mp3", ".zip", ".rar", ".docx", ".xlsx", ".pptx",
    ".css", ".js", ".xml", ".rss",
}

# URL patterns that indicate non-business pages
_SKIP_PATTERNS = (
    "/forum", "/thread", "/topic", "/community", "/wiki",
    "/blog/tag", "/category/", "/tag/", "/archive/",
    "translate.google", "webcache.google",
)

# Sub-paths to try for contact info in pass 2 — keep short, avoid duplicates
CONTACT_PATHS = ["/contact", "/about"]


def _should_skip(url: str) -> bool:
    if any(d in url for d in SKIP_DOMAINS):
        return True
    url_lower = url.lower().split("?")[0]   # strip query string for ext check
    if any(url_lower.endswith(ext) for ext in _SKIP_EXTENSIONS):
        return True
    if any(p in url_lower for p in _SKIP_PATTERNS):
        return True
    return False


def _base_url(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


async def _fetch_page(url: str, browser, js_wait_ms: int = 1500) -> str:
    """Load a page, wait for JS to render, return cleaned text."""
    page = None
    try:
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        })
        await page.goto(url, timeout=SCRAPER_PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
        # Wait for JS to render dynamic content
        await page.wait_for_timeout(js_wait_ms)
        html = await page.content()
        await page.close()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "meta"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return truncate_text(text, MAX_PAGE_TEXT_CHARS)
    except Exception as e:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        return f"ERROR:{e}"


async def _scrape_all(urls: list[str], run_id: int) -> list[dict]:
    results: list[dict] = []
    contact_urls: list[str] = []   # queued for pass 2

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ── Pass 1: main URLs ─────────────────────────────────────────────────
        skipped = sum(1 for u in urls if _should_skip(u))
        valid_urls = [u for u in urls if not _should_skip(u)]
        if skipped:
            log_agent_step(run_id, "ScraperAgent",
                           f"Pre-filter: skipped {skipped} PDF/image/forum URLs.")
        log_agent_step(run_id, "ScraperAgent", f"Pass 1 — scraping {len(valid_urls)} URLs.")

        for url in valid_urls:
            log_agent_step(run_id, "ScraperAgent", f"Scraping: {url}")
            text = None
            for attempt in (1, 2):   # 1 retry on failure
                try:
                    text = await asyncio.wait_for(
                        _fetch_page(url, browser, js_wait_ms=1500),
                        timeout=SCRAPER_HARD_TIMEOUT_SEC,
                    )
                    if not text.startswith("ERROR"):
                        break
                    if attempt == 1:
                        log_agent_step(run_id, "ScraperAgent",
                                       f"Retrying {url} (attempt 2)...", "WARNING")
                except asyncio.TimeoutError:
                    if attempt == 1:
                        log_agent_step(run_id, "ScraperAgent",
                                       f"Timeout on attempt 1, retrying {url}...", "WARNING")
                        text = "ERROR:timeout"
                    else:
                        log_agent_step(run_id, "ScraperAgent",
                                       f"Hard timeout after retry: {url}", "WARNING")
                        text = "ERROR:timeout"
                    continue

            if text and not text.startswith("ERROR"):
                results.append({"url": url, "text": text})
                log_agent_step(run_id, "ScraperAgent", f"OK — {len(text)} chars from {url}")
                # Queue contact sub-pages for pass 2
                base = _base_url(url)
                for path in CONTACT_PATHS:
                    contact_urls.append(urljoin(base, path))
            else:
                log_agent_step(run_id, "ScraperAgent",
                               f"Failed after retry: {url} → {(text or '')[:80]}", "WARNING")

        # ── Pass 2: contact/about sub-pages ───────────────────────────────────
        # Only 2 sub-paths per domain, cap total at 20, skip if same content as main page
        scraped_urls    = {r["url"] for r in results}
        scraped_content = {r["text"][:200] for r in results}  # content fingerprints

        contact_urls = list(dict.fromkeys(
            u for u in contact_urls if u not in scraped_urls and not _should_skip(u)
        ))[:20]

        log_agent_step(run_id, "ScraperAgent",
                       f"Pass 2 — checking {len(contact_urls)} contact/about sub-pages for phones & emails.")

        for url in contact_urls:
            try:
                text = await asyncio.wait_for(
                    _fetch_page(url, browser, js_wait_ms=800),
                    timeout=12,
                )
            except asyncio.TimeoutError:
                continue

            if not text.startswith("ERROR") and len(text) > 100:
                # Skip if this is the same content we already have (different URL, same page)
                fingerprint = text[:200]
                if fingerprint in scraped_content:
                    continue
                scraped_content.add(fingerprint)
                results.append({"url": url, "text": text})
                log_agent_step(run_id, "ScraperAgent",
                               f"Contact page OK — {len(text)} chars from {url}")

        await browser.close()

    log_agent_step(run_id, "ScraperAgent",
                   f"Total pages collected: {len(results)} (pass1 + contact sub-pages).")
    return results


def run_scraper_agent(state: dict) -> dict:
    run_id = state.get("run_id", 0)
    urls: list[str] = state.get("urls", [])

    log_agent_step(run_id, "ScraperAgent", f"Starting scraping for {len(urls)} URLs.")

    if not urls:
        log_agent_step(run_id, "ScraperAgent", "No URLs to scrape.", "WARNING")
        state["pages"] = []
        return state

    try:
        loop = asyncio.new_event_loop()
        pages = loop.run_until_complete(_scrape_all(urls, run_id))
        loop.close()
    except Exception as e:
        log_agent_step(run_id, "ScraperAgent", f"Scraper error: {e}", "ERROR")
        pages = []

    state["pages"] = pages
    return state
