"""
Google Maps / Google Business Profile Provider — free, uses Playwright.
Searches Google Maps and extracts:
  - Business name
  - Phone number
  - Website URL
  - Address
Returns structured leads directly (no LLM needed).
"""
import asyncio
import re
from playwright.async_api import async_playwright

MAPS_TIMEOUT = 15000   # ms
SCROLL_TIMES  = 4      # how many times to scroll the results panel


def _clean_phone(text: str) -> str:
    match = re.search(r"[\+\d][\d\s\-\(\)]{6,20}", text)
    return match.group().strip() if match else ""


async def _scrape_maps(query: str, max_results: int = 15) -> list[dict]:
    leads: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        })

        try:
            maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            await page.goto(maps_url, timeout=MAPS_TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)

            # Scroll the results panel to load more listings
            for _ in range(SCROLL_TIMES):
                await page.evaluate(
                    "document.querySelector('[role=\"feed\"]')?.scrollBy(0, 1000)"
                )
                await page.wait_for_timeout(1000)

            # Each business card in Maps
            cards = await page.query_selector_all('[role="feed"] > div > div > a')

            for card in cards[:max_results]:
                try:
                    # Click card to open details panel
                    await card.click()
                    await page.wait_for_timeout(1500)

                    # Business name
                    name_el = await page.query_selector('h1.DUwDvf, h1[class*="fontHeadlineLarge"]')
                    name    = (await name_el.inner_text()).strip() if name_el else ""

                    # Phone — look for tel: links or aria-label containing phone
                    phone = ""
                    phone_el = await page.query_selector('[data-tooltip="Copy phone number"], [aria-label*="Phone"]')
                    if phone_el:
                        phone = (await phone_el.get_attribute("aria-label") or "").replace("Phone:", "").strip()
                    if not phone:
                        # fallback: scan all text for phone-like patterns
                        body_text = await page.inner_text("body")
                        phone = _clean_phone(body_text)

                    # Website
                    website = ""
                    web_el = await page.query_selector('a[data-item-id="authority"]')
                    if web_el:
                        website = await web_el.get_attribute("href") or ""

                    # Address
                    address = ""
                    addr_el = await page.query_selector('[data-item-id="address"]')
                    if addr_el:
                        address = (await addr_el.inner_text()).strip()

                    if name:
                        leads.append({
                            "name":     "",
                            "company":  name,
                            "role":     "",
                            "email":    "",
                            "phone":    phone,
                            "linkedin": "",
                            "industry": "",
                            "location": address,
                            "source":   "google_maps",
                            "website":  website,
                        })
                except Exception:
                    continue

        except Exception:
            pass
        finally:
            await browser.close()

    return leads


def scrape_maps_leads(query: str, max_results: int = 15) -> list[dict]:
    """Synchronous wrapper — called from Search Agent thread."""
    try:
        loop = asyncio.new_event_loop()
        leads = loop.run_until_complete(_scrape_maps(query, max_results))
        loop.close()
        return leads
    except Exception:
        return []
