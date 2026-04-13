import reflex as rx
import sys, os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leadforge_ui.state.auth import AuthState
from database.sqlite_db import (
    get_all_leads,
    get_agent_runs,
    get_email_campaigns,
    get_all_sends,
)


class StageSummary(TypedDict):
    stage: str
    count: int
    pct_str: str


class IndustryData(TypedDict):
    industry: str
    count: int
    pct_str: str


class CampaignData(TypedDict):
    name: str
    sent: int
    status: str


class RecentRun(TypedDict):
    run_time: str
    status: str
    leads_found: int
    mode: str
    notes: str


class DashboardState(AuthState):
    """Metrics and chart data for the main dashboard."""

    # ── KPI cards ──────────────────────────────────────────────────────────────
    total_leads: int = 0
    new_leads: int = 0
    emails_sent: int = 0
    replies: int = 0

    # ── Pipeline stage summary (for bar chart) ─────────────────────────────────
    stage_summary: list[StageSummary] = []

    # ── Leads by industry (for pie/bar chart) ─────────────────────────────────
    industry_data: list[IndustryData] = []

    # ── Campaign performance ───────────────────────────────────────────────────
    campaign_data: list[CampaignData] = []

    # ── Recent runs ────────────────────────────────────────────────────────────
    recent_runs: list[RecentRun] = []

    # ── Loading ────────────────────────────────────────────────────────────────
    loading: bool = False

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_dashboard(self):
        self.loading = True
        self._compute_metrics()
        self.loading = False

    def _compute_metrics(self):
        leads = get_all_leads(user_id=self.user_id)

        self.total_leads = len(leads)
        self.new_leads = sum(
            1 for l in leads if (l.get("stage") or "new").lower() == "new"
        )

        sends = get_all_sends(self.user_id)
        self.emails_sent = len(sends)
        self.replies = sum(
            1 for s in sends if s.get("status") in ("replied", "auto_reply")
        )

        # Stage summary — pct_str precomputed so components don't need f-strings
        stage_counts: dict[str, int] = {}
        for l in leads:
            s = (l.get("stage") or "New").capitalize()
            stage_counts[s] = stage_counts.get(s, 0) + 1
        max_stage = max(stage_counts.values()) if stage_counts else 1
        self.stage_summary = [
            {"stage": k, "count": v, "pct_str": f"{int(v / max_stage * 100)}%"}
            for k, v in stage_counts.items()
        ]

        # Industry data (top 8) — pct_str precomputed
        ind_counts: dict[str, int] = {}
        for l in leads:
            ind = l.get("industry") or "Unknown"
            ind_counts[ind] = ind_counts.get(ind, 0) + 1
        sorted_ind = sorted(ind_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        max_ind = sorted_ind[0][1] if sorted_ind else 1
        self.industry_data = [
            {"industry": k, "count": v, "pct_str": f"{int(v / max_ind * 100)}%"}
            for k, v in sorted_ind
        ]

        # Campaign performance
        campaigns = get_email_campaigns(self.user_id)
        self.campaign_data = [
            {
                "name": c.get("name") or "",
                "sent": int(c.get("sent_count") or 0),
                "status": c.get("status") or "draft",
            }
            for c in campaigns[:10]
        ]

        # Recent runs — normalize to match RecentRun TypedDict
        runs = get_agent_runs(user_id=self.user_id)
        self.recent_runs = [
            {
                "run_time": str(r.get("run_time") or ""),
                "status": str(r.get("status") or ""),
                "leads_found": int(r.get("leads_found") or 0),
                "mode": str(r.get("mode") or ""),
                "notes": str(r.get("notes") or ""),
            }
            for r in runs[:5]
        ]
