"""
Database Agent
Saves enriched leads into SQLite.
Filters: skips 0-contact leads and leads already in DB for this product.
"""
from database.sqlite_db import save_leads, log_agent_step, lead_email_exists


def run_db_agent(state: dict) -> dict:
    run_id     = state.get("run_id", 0)
    product_id = state.get("product_id")
    enriched_leads: list[dict] = state.get("enriched_leads", [])

    log_agent_step(run_id, "DBAgent", f"{len(enriched_leads)} leads before filters (product_id={product_id}).")

    # ── Filter 1: drop leads with no email AND no phone (0-contact) ───────────
    contactable = [l for l in enriched_leads if l.get("email") or l.get("phone")]
    dropped_contact = len(enriched_leads) - len(contactable)
    if dropped_contact:
        log_agent_step(run_id, "DBAgent",
                       f"Dropped {dropped_contact} leads with no email and no phone.")

    # ── Filter 2: cross-run deduplication (skip if email already in DB) ───────
    to_save = []
    skipped_dup = 0
    for lead in contactable:
        email = lead.get("email", "")
        if email and lead_email_exists(product_id, email):
            skipped_dup += 1
        else:
            to_save.append(lead)
    if skipped_dup:
        log_agent_step(run_id, "DBAgent",
                       f"Skipped {skipped_dup} leads already in DB (cross-run dedup).")

    log_agent_step(run_id, "DBAgent", f"Saving {len(to_save)} new leads to SQLite.")

    try:
        save_leads(to_save, product_id=product_id, run_id=run_id)
        log_agent_step(run_id, "DBAgent", f"Successfully saved {len(to_save)} leads.")
        state["leads_saved"] = len(to_save)
    except Exception as e:
        log_agent_step(run_id, "DBAgent", f"Error saving leads: {e}", "ERROR")
        state["leads_saved"] = 0

    return state
