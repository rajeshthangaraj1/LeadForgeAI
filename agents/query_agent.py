"""
Query Agent
Uses Ollama LLM to generate short, human-like DuckDuckGo search queries.
Falls back to template-based queries if LLM is unavailable.
"""
import json
from database.sqlite_db import log_agent_step
from config.settings import QUERY_TEMPERATURE, MAX_SEARCH_QUERIES
from utils.llm_utils import call_ollama, extract_json_array

QUERY_PROMPT = """You are a lead generation expert for {biz_type} businesses.

Given this target audience, generate exactly 12 short DuckDuckGo search queries to find leads.

Target Audience:
- Industry: {industry}
- Country: {country}
- Location: {location}
- Roles: {roles}
- Keywords: {keywords}
- Competitors: {competitors}
- Business Type: {biz_type}

Rules:
- Each query must be SHORT (4-7 words max)
- No site:linkedin.com queries (they hang)
- Use only the FIRST industry value and country name
- For B2B: focus on company directories, decision maker contacts, business email lists
- For B2C: focus on consumer directories, service providers, local business listings
- For Both: mix B2B and B2C queries
- Mix of: company discovery + contact finding + email/phone search

Return ONLY a JSON array of 12 strings. Example:
["logistics companies Dubai", "warehouse companies UAE email", ...]

JSON array:"""



def _template_queries(plan: dict) -> list[str]:
    """Fallback: template-based short queries."""
    industries = [x.strip() for x in plan.get("industry", "").split(",") if x.strip()]
    locations  = [x.strip() for x in plan.get("location", "").split(",")  if x.strip()]
    roles      = plan.get("roles", [])
    keywords   = plan.get("keywords", [])
    competitors = plan.get("competitors", [])

    ind = industries[0] if industries else "business"
    loc = locations[0]  if locations  else ""

    queries = []
    if ind and loc:
        queries += [
            f"{ind} companies {loc}",
            f"{ind} companies {loc} contact email",
            f"top {ind} companies in {loc}",
            f"{ind} business directory {loc}",
            f"{ind} companies {loc} email list",
        ]
    for role in (roles[:2] if isinstance(roles, list) else []):
        if loc:
            queries.append(f"{role} {ind} {loc} email")
    for kw in (keywords[:2] if isinstance(keywords, list) else []):
        queries.append(f"{kw} companies {loc}" if loc else f"{kw} companies email")
    for comp in (competitors[:1] if isinstance(competitors, list) else []):
        queries.append(f"companies like {comp} {ind}")
    # extra locations
    if len(locations) > 1:
        queries.append(f"{ind} companies {locations[1]}")

    return list(dict.fromkeys(q for q in queries if q.strip()))[:15]


def run_query_agent(state: dict) -> dict:
    run_id = state.get("run_id", 0)
    plan: dict = state.get("plan", {})

    log_agent_step(run_id, "QueryAgent", "Asking Ollama LLM to generate search queries...")

    biz_type = plan.get("business_type", "B2B") or "B2B"
    country  = plan.get("country", "") or plan.get("location", "")
    log_agent_step(run_id, "QueryAgent",
                   f"Business Type: {biz_type} | Country: {country}")

    prompt = QUERY_PROMPT.format(
        industry    = plan.get("industry", ""),
        country     = country,
        location    = plan.get("location", ""),
        roles       = ", ".join(plan.get("roles", [])),
        keywords    = ", ".join(plan.get("keywords", [])),
        competitors = ", ".join(plan.get("competitors", [])),
        biz_type    = biz_type,
    )

    raw, err = call_ollama(prompt, temperature=QUERY_TEMPERATURE, num_predict=500, timeout=60)
    queries: list[str] = []

    if err:
        log_agent_step(run_id, "QueryAgent", f"Ollama unavailable ({err}), using template queries.", "WARNING")
        queries = _template_queries(plan)
    else:
        try:
            json_str = extract_json_array(raw)
            if not json_str:
                raise ValueError("No JSON array found")
            queries = json.loads(json_str)
            if not isinstance(queries, list):
                raise ValueError("Not a list")
            queries = [q for q in queries if isinstance(q, str) and "linkedin.com" not in q and len(q) < 80]
            queries = queries[:15]
            log_agent_step(run_id, "QueryAgent", f"LLM generated {len(queries)} queries.")
        except Exception as e:
            log_agent_step(run_id, "QueryAgent", f"LLM parse failed ({e}), using template queries.", "WARNING")
            queries = _template_queries(plan)

    # Final dedup
    queries = list(dict.fromkeys(q.strip() for q in queries if q.strip()))[:MAX_SEARCH_QUERIES]

    for q in queries:
        log_agent_step(run_id, "QueryAgent", f"  → {q}")

    state["queries"] = queries
    return state
