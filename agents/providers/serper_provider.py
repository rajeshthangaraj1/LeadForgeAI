"""
Serper.dev Provider — Google Search results via API.
2500 free queries then paid. Get API key at serper.dev.
Enable by adding API key in Search Providers settings.
"""
import httpx
from config.settings import MAX_URLS_PER_QUERY


def search(query: str, api_key: str, max_results: int = MAX_URLS_PER_QUERY) -> list[str]:
    if not api_key:
        return []
    try:
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results},
            timeout=10,
        )
        resp.raise_for_status()
        data    = resp.json()
        organic = data.get("organic", [])
        return [r["link"] for r in organic if r.get("link")]
    except Exception:
        return []
