import reflex as rx
from typing import TypedDict
from leadforge_ui.components.layout import layout
from leadforge_ui.components.cards import stat_card, info_card
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.base_state import AppState
from leadforge_ui.styles.theme import PRIMARY, SUCCESS, WARNING, CARD_STYLE, BORDER
from collections import Counter


class ChartBar(TypedDict):
    name: str
    value: int
    pct_str: str


class SendsBar(TypedDict):
    date: str
    sent: int
    pct_str: str


class CampaignRate(TypedDict):
    name: str
    rate: float
    rate_str: str
    pct_str: str


class AnalyticsState(AuthState):
    """Analytics page state — chart data derived from leads + sends."""

    # Leads by industry
    industry_chart: list[ChartBar] = []
    # Leads by location
    location_chart: list[ChartBar] = []
    # Emails sent over time
    sends_over_time: list[SendsBar] = []
    # Reply rate per campaign
    campaign_reply_rates: list[CampaignRate] = []

    total_leads: int = 0
    total_emails: int = 0
    total_replies: int = 0
    overall_reply_rate: float = 0.0

    @rx.var
    def reply_rate_str(self) -> str:
        return f"{self.overall_reply_rate}%"

    def load_analytics(self):
        from database.sqlite_db import get_all_leads, get_all_sends, get_email_campaigns, get_campaign_analytics
        leads = get_all_leads(user_id=self.user_id)
        self.total_leads = len(leads)

        # Industry chart (top 12) — pct_str precomputed
        ind = Counter(l.get("industry") or "Unknown" for l in leads)
        ind_top = ind.most_common(12)
        max_ind = ind_top[0][1] if ind_top else 1
        self.industry_chart = [
            {"name": k, "value": v, "pct_str": f"{int(v / max_ind * 100)}%"}
            for k, v in ind_top
        ]

        # Location chart (top 12) — pct_str precomputed
        loc = Counter(l.get("location") or "Unknown" for l in leads)
        loc_top = loc.most_common(12)
        max_loc = loc_top[0][1] if loc_top else 1
        self.location_chart = [
            {"name": k, "value": v, "pct_str": f"{int(v / max_loc * 100)}%"}
            for k, v in loc_top
        ]

        # Email sends
        sends = get_all_sends(self.user_id)
        self.total_emails = len(sends)
        replies = sum(1 for s in sends if s.get("status") in ("replied", "auto_reply"))
        self.total_replies = replies
        self.overall_reply_rate = round(replies / len(sends) * 100, 1) if sends else 0.0

        # Sends over time (by date, last 30) — pct_str precomputed
        date_counts: dict[str, int] = {}
        for s in sends:
            date = (s.get("sent_at") or "")[:10]
            if date:
                date_counts[date] = date_counts.get(date, 0) + 1
        sorted_dates = sorted(date_counts.items())[-30:]
        max_sent = max(v for _, v in sorted_dates) if sorted_dates else 1
        self.sends_over_time = [
            {"date": k, "sent": v, "pct_str": f"{int(v / max_sent * 100)}%"}
            for k, v in sorted_dates
        ]

        # Campaign reply rates — pct_str and rate_str precomputed
        campaigns = get_email_campaigns(self.user_id)
        rates = []
        for c in campaigns[:8]:
            rate = get_campaign_analytics(c["id"])["reply_rate"]
            rates.append({
                "name": c["name"][:20],
                "rate": rate,
                "rate_str": f"{rate}%",
                "pct_str": f"{min(int(rate * 3), 100)}%",
            })
        self.campaign_reply_rates = rates


# ── Chart helpers ─────────────────────────────────────────────────────────────

def horizontal_bar(item, color: str = PRIMARY) -> rx.Component:
    return rx.hstack(
        rx.text(item["name"], size="2", color="#374151", width="160px", no_of_lines=1),
        rx.box(
            rx.box(height="10px", border_radius="5px", background_color=color, width=item["pct_str"]),
            background_color="#f3f4f6",
            border_radius="5px",
            height="10px",
            flex="1",
        ),
        rx.text(item["value"], size="2", color="#6b7280", width="32px", text_align="right"),
        align="center",
        spacing="3",
        width="100%",
    )


def sends_bar(item) -> rx.Component:
    return rx.hstack(
        rx.text(item["date"], size="1", color="#374151", width="80px"),
        rx.box(
            rx.box(height="16px", border_radius="4px", background_color=WARNING, width=item["pct_str"]),
            background_color="#f3f4f6",
            border_radius="4px",
            height="16px",
            flex="1",
        ),
        rx.text(item["sent"], size="1", color="#6b7280", width="28px", text_align="right"),
        align="center",
        spacing="2",
        width="100%",
    )


def campaign_rate_row(item) -> rx.Component:
    return rx.hstack(
        rx.text(item["name"], size="2", color="#374151", width="120px"),
        rx.box(
            rx.box(
                height="10px",
                border_radius="5px",
                background_color=SUCCESS,
                width=item["pct_str"],
                max_width="200px",
            ),
            background_color="#f3f4f6",
            border_radius="5px",
            height="10px",
            flex="1",
        ),
        rx.text(item["rate_str"], size="2", color="#6b7280", width="40px", text_align="right"),
        align="center",
        spacing="3",
        width="100%",
    )


# ── Analytics content ─────────────────────────────────────────────────────────

def analytics_content() -> rx.Component:
    return rx.vstack(
        # ── KPI row ───────────────────────────────────────────────────────────
        rx.grid(
            stat_card("Total Leads",  AnalyticsState.total_leads,    "users",   PRIMARY),
            stat_card("Emails Sent",  AnalyticsState.total_emails,   "mail",    WARNING),
            stat_card("Replies",      AnalyticsState.total_replies,  "reply",   SUCCESS),
            stat_card("Reply Rate",   AnalyticsState.reply_rate_str, "percent", "#8b5cf6"),
            columns="4",
            spacing="5",
            width="100%",
        ),

        # ── Charts row 1: Industry | Location ─────────────────────────────────
        rx.grid(
            info_card(
                "Leads by Industry",
                rx.vstack(
                    rx.foreach(
                        AnalyticsState.industry_chart,
                        lambda item: horizontal_bar(item, PRIMARY),
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            info_card(
                "Leads by Location",
                rx.vstack(
                    rx.foreach(
                        AnalyticsState.location_chart,
                        lambda item: horizontal_bar(item, "#8b5cf6"),
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="5",
            width="100%",
        ),

        # ── Charts row 2: Sends over time | Campaign reply rates ──────────────
        rx.grid(
            info_card(
                "Emails Sent Over Time",
                rx.vstack(
                    rx.foreach(AnalyticsState.sends_over_time, sends_bar),
                    spacing="2",
                    width="100%",
                ),
            ),
            info_card(
                "Campaign Reply Rates",
                rx.vstack(
                    rx.foreach(AnalyticsState.campaign_reply_rates, campaign_rate_row),
                    spacing="3",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="5",
            width="100%",
        ),

        spacing="6",
        width="100%",
    )


@rx.page(
    route="/analytics",
    on_load=[AuthState.check_auth, AppState.load_products, AnalyticsState.load_analytics],
)
def analytics():
    return layout(
        analytics_content(),
        title="Analytics",
        subtitle="Leads, campaigns and pipeline performance",
    )
