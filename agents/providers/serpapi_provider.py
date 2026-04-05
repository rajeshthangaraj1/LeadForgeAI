"""
SerpAPI Provider — Google Search results via API.
100 free searches/month then paid. Get API key at serpapi.com.
Enable by adding API key in Search Providers settings.
"""
import httpx
from config.settings import MAX_URLS_PER_QUERY


def search(query: str, api_key: str, max_results: int = MAX_URLS_PER_QUERY) -> list[str]:
    if not api_key:
        return []
    try:
        resp = httpx.get(
            "https://serpapi.com/search",
            params={
                "q":       query,
                "api_key": api_key,
                "engine":  "google",
                "num":     max_results,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data    = resp.json()
        results = data.get("organic_results", [])
        return [r["link"] for r in results if r.get("link")]
    except Exception:
        return []
