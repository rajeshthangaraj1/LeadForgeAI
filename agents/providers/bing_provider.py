"""
Bing Search Provider — uses Playwright (headless) since Bing is fully JS-rendered.
httpx/requests only get an empty shell — no links in static HTML.
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config.settings import MAX_URLS_PER_QUERY

SKIP_DOMAINS = {
    "bing.com", "microsoft.com", "msn.com",
    "go.microsoft.com", "support.microsoft.com",
    "linkedin.com", "facebook.com", "twitter.com",
}


async def _search_async(query: str, max_results: int) -> list[str]:
    urls: list[str] = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            })
            await page.goto(
                f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=20&setlang=en",
                timeout=15000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(1500)
            html  = await page.content()
            await browser.close()

            soup = BeautifulSoup(html, "html.parser")
            for li in soup.select("li.b_algo"):
                a = li.select_one("h2 a") or li.select_one("a[href]")
                if not a:
                    continue
                href = a.get("href", "")
                if href.startswith("http") and not any(d in href for d in SKIP_DOMAINS):
                    urls.append(href)
                if len(urls) >= max_results:
                    break

            # Fallback — grab all external links if CSS selector found nothing
            if not urls:
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http") and not any(d in href for d in SKIP_DOMAINS):
                        if href not in urls:
                            urls.append(href)
                    if len(urls) >= max_results:
                        break

    except Exception:
        pass
    return urls


def search(query: str, max_results: int = MAX_URLS_PER_QUERY) -> list[str]:
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_search_async(query, max_results))
        loop.close()
        return result
    except Exception:
        return []
