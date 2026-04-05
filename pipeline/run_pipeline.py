"""
Pipeline Runner
Entry point to execute the full LangGraph agent pipeline.
mode = 'start'  → clears existing leads for this product before running
mode = 'rerun'  → keeps existing leads, just appends new ones
"""
import config.settings as _cfg
from database.sqlite_db import create_agent_run, log_agent_step, clear_leads
from graph.agent_graph import get_graph


def run_pipeline(product_id: int, mode: str = "start") -> dict:
    # 'start' clears old leads for this product; 'rerun' keeps them
    if mode == "start":
        clear_leads(product_id=product_id)

    run_id = create_agent_run(product_id=product_id, mode=mode)
    log_agent_step(
        run_id, "Pipeline",
        f"Starting LeadForge AI pipeline (run_id={run_id}, product_id={product_id}, mode={mode})."
    )
    log_agent_step(
        run_id, "Pipeline",
        f"LLM model: {_cfg.OLLAMA_MODEL}  |  Ollama URL: {_cfg.OLLAMA_BASE_URL}"
    )

    initial_state = {"run_id": run_id, "product_id": product_id, "mode": mode}

    try:
        graph = get_graph()
        final_state = graph.invoke(initial_state)
        report = final_state.get("report", {})
        log_agent_step(run_id, "Pipeline", f"Pipeline finished — {report.get('leads_found', 0)} leads saved.")
        return {"run_id": run_id, **report}
    except Exception as e:
        log_agent_step(run_id, "Pipeline", f"Unhandled pipeline error: {e}", "ERROR")
        return {"run_id": run_id, "status": "failed", "error": str(e), "leads_found": 0}
