"""
Reporter Agent
Uses Ollama LLM to generate a human-readable run summary report.
"""
from collections import Counter
from database.sqlite_db import log_agent_step, update_agent_run
from config.settings import REPORTER_TEMPERATURE
from utils.llm_utils import call_ollama

REPORT_PROMPT = """You are a B2B sales intelligence AI.

A lead generation pipeline just completed. Here is the summary data:

- Total leads found: {leads_found}
- Top industries: {top_industries}
- Top locations: {top_locations}
- Top companies: {top_companies}
- Top roles: {top_roles}
- ICP (Ideal Customer Profile): {icp}

Write a short, professional 3-4 sentence executive summary of these results.
Mention what was found, the quality of leads, and a recommended next action.
Be direct and concise. Return ONLY the summary text, no headers."""



def run_reporter_agent(state: dict) -> dict:
    run_id = state.get("run_id", 0)
    enriched_leads: list[dict] = state.get("enriched_leads", [])
    leads_saved: int = state.get("leads_saved", 0)
    error: str = state.get("error", "")
    plan: dict = state.get("plan", {})

    if error:
        log_agent_step(run_id, "ReporterAgent", f"Pipeline ended with error: {error}", "ERROR")
        update_agent_run(run_id, "failed", 0, error)
        state["report"] = {"status": "failed", "error": error, "leads_found": 0}
        return state

    # Build analytics
    companies  = [l.get("company", "") for l in enriched_leads if l.get("company")]
    industries = [l.get("industry", "") for l in enriched_leads if l.get("industry")]
    locations  = [l.get("location", "") for l in enriched_leads if l.get("location")]
    roles      = [l.get("role", "") for l in enriched_leads if l.get("role")]

    top_companies  = Counter(companies).most_common(8)
    top_industries = Counter(industries).most_common(5)
    top_locations  = Counter(locations).most_common(5)
    top_roles      = Counter(roles).most_common(5)

    # Ask LLM to write executive summary
    log_agent_step(run_id, "ReporterAgent", "Asking Ollama LLM for executive summary...")
    summary, _ = call_ollama(REPORT_PROMPT.format(
        leads_found    = leads_saved,
        top_industries = top_industries,
        top_locations  = top_locations,
        top_companies  = top_companies,
        top_roles      = top_roles,
        icp            = plan.get("icp", "Not specified"),
    ), temperature=REPORTER_TEMPERATURE, num_predict=300, timeout=40)

    if summary:
        log_agent_step(run_id, "ReporterAgent", f"LLM summary received ({len(summary)} chars).")
    else:
        log_agent_step(run_id, "ReporterAgent",
                       "LLM summary unavailable — using fallback text.", "WARNING")
        summary = (
            f"Pipeline completed successfully. {leads_saved} leads collected across "
            f"{len(set(companies))} companies in {len(set(industries))} industries "
            f"primarily from {top_locations[0][0] if top_locations else 'unknown'} region."
        )

    notes = (
        f"Summary: {summary} | "
        f"Top industries: {top_industries} | "
        f"Top locations: {top_locations}"
    )

    log_agent_step(run_id, "ReporterAgent", f"Run complete — {leads_saved} leads saved.")
    log_agent_step(run_id, "ReporterAgent", f"Executive Summary: {summary}")

    update_agent_run(run_id, "completed", leads_saved, notes)

    state["report"] = {
        "status":        "completed",
        "leads_found":   leads_saved,
        "summary":       summary,
        "top_companies": top_companies,
        "top_industries":top_industries,
        "top_locations": top_locations,
        "top_roles":     top_roles,
    }
    return state
