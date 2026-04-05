"""
DuckDuckGo Search Provider — free, no API key.
"""
from config.settings import MAX_URLS_PER_QUERY

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


def search(query: str, max_results: int = MAX_URLS_PER_QUERY) -> list[str]:
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        return [r["href"] for r in results if r.get("href")]
    except Exception:
        return []
