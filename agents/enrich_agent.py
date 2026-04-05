"""
Enrichment Agent
Uses Ollama LLM to enrich each lead with industry, company size, segment, B2B/B2C.
"""
import json
from database.sqlite_db import log_agent_step
from utils.helpers import chunk_list
from config.settings import ENRICH_TEMPERATURE, ENRICH_BATCH_SIZE
from utils.llm_utils import call_ollama, extract_json_array

ENRICH_PROMPT = """You are a B2B data enrichment AI.

Given these business leads (JSON), add or improve:
- industry: industry sector
- segment: sub-segment (e.g. "SaaS", "FinTech", "E-commerce")
- company_size: estimated size ("1-10", "11-50", "51-200", "201-500", "500+")
- biz_type: "B2B", "B2C", or "Both"

Return ONLY a JSON array with the same leads enriched. Do not add or remove leads.

Leads:
{leads_json}

Enriched JSON:"""


def _enrich_batch(leads: list[dict], run_id: int) -> list[dict]:
    prompt = ENRICH_PROMPT.format(leads_json=json.dumps(leads, indent=2))
    raw, err = call_ollama(prompt, temperature=ENRICH_TEMPERATURE, num_predict=1500, timeout=90)

    if err:
        log_agent_step(run_id, "EnrichAgent", f"Ollama error: {err}", "WARNING")
        return leads

    try:
        json_str = extract_json_array(raw)
        if not json_str:
            return leads
        enriched = json.loads(json_str)
        if isinstance(enriched, list) and len(enriched) == len(leads):
            return enriched
        return leads
    except Exception:
        return leads


def _needs_enrichment(lead: dict) -> bool:
    """Skip LLM if we already have industry AND a company name — Maps leads qualify."""
    has_industry = bool(lead.get("industry", "").strip())
    has_company  = bool(lead.get("company", "").strip())
    return not (has_industry and has_company)


def run_enrich_agent(state: dict) -> dict:
    run_id = state.get("run_id", 0)
    cleaned_leads: list[dict] = state.get("cleaned_leads", [])

    # Split: leads that need enrichment vs already complete
    to_enrich = [l for l in cleaned_leads if _needs_enrichment(l)]
    already_ok = [l for l in cleaned_leads if not _needs_enrichment(l)]

    log_agent_step(run_id, "EnrichAgent",
                   f"{len(cleaned_leads)} leads total — "
                   f"{len(to_enrich)} need enrichment, "
                   f"{len(already_ok)} already complete (skipping LLM).")

    enriched_all: list[dict] = list(already_ok)  # pass through as-is

    if to_enrich:
        batches = chunk_list(to_enrich, ENRICH_BATCH_SIZE)
        for i, batch in enumerate(batches):
            log_agent_step(run_id, "EnrichAgent",
                           f"Enriching batch {i + 1}/{len(batches)} ({len(batch)} leads).")
            enriched = _enrich_batch(batch, run_id)
            enriched_all.extend(enriched)

    log_agent_step(run_id, "EnrichAgent", f"Enrichment complete for {len(enriched_all)} leads.")
    state["enriched_leads"] = enriched_all
    return state
