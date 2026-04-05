"""
Brave Search API Provider — paid (2000 free/month).
Enable by adding API key from brave.com/search/api in Search Providers settings.
"""
import httpx
from config.settings import MAX_URLS_PER_QUERY


def search(query: str, api_key: str, max_results: int = MAX_URLS_PER_QUERY) -> list[str]:
    if not api_key:
        return []
    try:
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            params={"q": query, "count": max_results},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        return [r["url"] for r in results if r.get("url")]
    except Exception:
        return []
