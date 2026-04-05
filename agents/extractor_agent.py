"""
Lead Extraction Agent
Uses Ollama LLM to extract structured lead data from scraped page text.
"""
import json
from database.sqlite_db import log_agent_step
from utils.helpers import truncate_text
from config.settings import EXTRACTOR_TEMPERATURE, MAX_PAGE_TEXT_CHARS
from utils.llm_utils import call_ollama, extract_json_array


EXTRACT_PROMPT = """You are a lead extraction AI. Read the following web page text and extract any business contacts or company information.

Return a JSON array of leads. Each lead must have these fields:
- name (person's full name or empty string)
- company (company name or empty string)
- role (job title or empty string)
- email (email address or empty string)
- phone (phone or mobile number with country code if visible, or empty string)
- linkedin (LinkedIn profile URL or empty string)
- industry (industry sector or empty string)
- location (city/country or empty string)

Rules:
- Only return valid JSON array, nothing else.
- If no leads found, return []
- Do not invent information.
- For phone: extract any number that looks like +971-50-123-4567 or 04-123456 or +1 800 555 0000

Page text:
{text}

JSON array of leads:"""


def _extract_leads_from_text(text: str, source_url: str, run_id: int) -> list[dict]:
    prompt = EXTRACT_PROMPT.format(text=truncate_text(text, MAX_PAGE_TEXT_CHARS))
    raw, err = call_ollama(prompt, temperature=EXTRACTOR_TEMPERATURE, num_predict=1000, timeout=90)

    if err:
        log_agent_step(run_id, "ExtractorAgent", f"Ollama error: {err}", "WARNING")
        return []

    try:
        json_str = extract_json_array(raw)
        if not json_str:
            return []
        leads = json.loads(json_str)
        if not isinstance(leads, list):
            return []
        for lead in leads:
            lead["source"] = source_url
        return leads
    except json.JSONDecodeError:
        log_agent_step(run_id, "ExtractorAgent", "JSON parse error from LLM response.", "WARNING")
        return []


def run_extractor_agent(state: dict) -> dict:
    run_id     = state.get("run_id", 0)
    pages      = state.get("pages", [])
    maps_leads = state.get("maps_leads", [])  # from Google Maps — already structured

    all_leads: list[dict] = []

    # Google Maps leads come in pre-structured — no LLM needed
    if maps_leads:
        log_agent_step(run_id, "ExtractorAgent",
                       f"Merging {len(maps_leads)} Google Maps leads (no LLM needed).")
        all_leads.extend(maps_leads)

    # Scraped pages — LLM extraction
    log_agent_step(run_id, "ExtractorAgent",
                   f"Extracting leads from {len(pages)} scraped pages via Ollama LLM.")
    for page in pages:
        url  = page.get("url", "")
        text = page.get("text", "")
        log_agent_step(run_id, "ExtractorAgent", f"Extracting from: {url}")
        leads = _extract_leads_from_text(text, url, run_id)
        log_agent_step(run_id, "ExtractorAgent", f"Found {len(leads)} leads on {url}")
        all_leads.extend(leads)

    log_agent_step(run_id, "ExtractorAgent",
                   f"Total raw leads: {len(all_leads)} "
                   f"({len(maps_leads)} Maps + {len(all_leads)-len(maps_leads)} LLM)")
    state["raw_leads"] = all_leads
    return state
