"""
Cleaner Agent
Removes duplicates, cleans emails, normalises company names, scores leads.
"""
from database.sqlite_db import log_agent_step
from utils.helpers import clean_email, clean_linkedin, clean_phone, normalize_company_name, deduplicate_leads


def _score_lead(lead: dict) -> int:
    """
    Score a lead 0-10 based on data completeness.
    Higher = more contactable / better quality.
    """
    score = 0
    if lead.get("email"):   score += 3   # email is most important
    if lead.get("phone"):   score += 2   # phone second
    if lead.get("company"): score += 2   # company name essential for B2B
    if lead.get("name"):    score += 1   # contact name
    if lead.get("industry"):score += 1   # helps targeting
    if lead.get("linkedin"):score += 1   # social proof
    return min(score, 10)


def run_cleaner_agent(state: dict) -> dict:
    run_id = state.get("run_id", 0)
    raw_leads: list[dict] = state.get("raw_leads", [])

    log_agent_step(run_id, "CleanerAgent", f"Cleaning {len(raw_leads)} raw leads.")

    cleaned: list[dict] = []
    for lead in raw_leads:
        c = {
                "name":     str(lead.get("name", "")).strip().title(),
                "company":  normalize_company_name(str(lead.get("company", ""))),
                "role":     str(lead.get("role", "")).strip().title(),
                "email":    clean_email(str(lead.get("email", ""))),
                "phone":    clean_phone(str(lead.get("phone", ""))),
                "linkedin": clean_linkedin(str(lead.get("linkedin", ""))),
                "industry": str(lead.get("industry", "")).strip().title(),
                "location": str(lead.get("location", "")).strip().title(),
                "source":   lead.get("source", ""),
        }
        c["score"] = _score_lead(c)
        cleaned.append(c)

    before = len(cleaned)
    cleaned = deduplicate_leads(cleaned)
    after = len(cleaned)

    high  = sum(1 for l in cleaned if l["score"] >= 7)
    med   = sum(1 for l in cleaned if 4 <= l["score"] < 7)
    low   = sum(1 for l in cleaned if l["score"] < 4)
    log_agent_step(
        run_id, "CleanerAgent",
        f"Cleaned: {before} → {after} leads (removed {before - after} dupes). "
        f"Quality — High(7-10):{high}  Medium(4-6):{med}  Low(0-3):{low}",
    )

    state["cleaned_leads"] = cleaned
    return state
