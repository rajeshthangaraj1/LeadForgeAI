"""
LangGraph Agent Workflow
Connects all agent nodes into a sequential pipeline.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

from agents.planner_agent import run_planner
from agents.query_agent import run_query_agent
from agents.search_agent import run_search_agent
from agents.scraper_agent import run_scraper_agent
from agents.extractor_agent import run_extractor_agent
from agents.cleaner_agent import run_cleaner_agent
from agents.enrich_agent import run_enrich_agent
from agents.db_agent import run_db_agent
from agents.reporter_agent import run_reporter_agent


class PipelineState(TypedDict, total=False):
    run_id: int
    product_id: int
    mode: str
    error: str
    plan: dict
    queries: list
    urls: list
    maps_leads: list   # Google Maps structured leads — passed direct to extractor
    pages: list
    raw_leads: list
    cleaned_leads: list
    enriched_leads: list
    leads_saved: int
    report: dict


def should_continue(state: PipelineState) -> str:
    """Stop early if an error was set."""
    if state.get("error"):
        return "reporter"
    return "continue"


def build_graph() -> StateGraph:
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("planner", run_planner)
    workflow.add_node("query", run_query_agent)
    workflow.add_node("search", run_search_agent)
    workflow.add_node("scraper", run_scraper_agent)
    workflow.add_node("extractor", run_extractor_agent)
    workflow.add_node("cleaner", run_cleaner_agent)
    workflow.add_node("enricher", run_enrich_agent)
    workflow.add_node("db", run_db_agent)
    workflow.add_node("reporter", run_reporter_agent)

    # Entry point
    workflow.set_entry_point("planner")

    # Edges with early-exit check after planner
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {"continue": "query", "reporter": "reporter"},
    )
    workflow.add_edge("query", "search")
    workflow.add_edge("search", "scraper")
    workflow.add_edge("scraper", "extractor")
    workflow.add_edge("extractor", "cleaner")
    workflow.add_edge("cleaner", "enricher")
    workflow.add_edge("enricher", "db")
    workflow.add_edge("db", "reporter")
    workflow.add_edge("reporter", END)

    return workflow.compile()


def get_graph():
    # Always rebuild — never cache, so schema changes take effect immediately
    return build_graph()
