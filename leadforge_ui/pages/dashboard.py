import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.components.cards import stat_card, info_card
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.dashboard_state import DashboardState
from leadforge_ui.styles.theme import PRIMARY, SUCCESS, WARNING, INFO, CARD_STYLE, BORDER


# ── Stage summary mini-list ────────────────────────────────────────────────────

def stage_row(item) -> rx.Component:
    return rx.hstack(
        rx.text(item["stage"], size="2", color="#374151", width="100px"),
        rx.box(
            rx.box(
                height="8px",
                border_radius="4px",
                background_color=PRIMARY,
                width=item["pct_str"],
            ),
            background_color="#f3f4f6",
            border_radius="4px",
            height="8px",
            flex="1",
        ),
        rx.text(item["count"], size="2", color="#6b7280", width="40px", text_align="right"),
        align="center",
        spacing="3",
        width="100%",
    )


# ── Industry chart (simple horizontal bars) ────────────────────────────────────

def industry_row(item) -> rx.Component:
    return rx.hstack(
        rx.text(item["industry"], size="2", color="#374151", width="140px", no_of_lines=1),
        rx.box(
            rx.box(
                height="8px",
                border_radius="4px",
                background_color="#8b5cf6",
                width=item["pct_str"],
            ),
            background_color="#f3f4f6",
            border_radius="4px",
            height="8px",
            flex="1",
        ),
        rx.text(item["count"], size="2", color="#6b7280", width="32px", text_align="right"),
        align="center",
        spacing="3",
        width="100%",
    )


# ── Recent runs table ─────────────────────────────────────────────────────────

def run_row(run) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(rx.cond(run["run_time"], run["run_time"][:16], "—"), size="2")),
        rx.table.cell(
            rx.match(
                run["status"],
                ("completed", rx.badge("Completed", color_scheme="green", variant="soft")),
                ("running",   rx.badge("Running",   color_scheme="blue",  variant="soft")),
                ("failed",    rx.badge("Failed",    color_scheme="red",   variant="soft")),
                rx.badge(run["status"], color_scheme="gray", variant="soft"),
            )
        ),
        rx.table.cell(rx.text(run["leads_found"], size="2")),
        rx.table.cell(rx.text(rx.cond(run["mode"], run["mode"], "—"), size="2")),
    )


# ── Dashboard content ─────────────────────────────────────────────────────────

def dashboard_content() -> rx.Component:
    return rx.vstack(
        # ── KPI cards ─────────────────────────────────────────────────────────
        rx.grid(
            stat_card("Total Leads",   DashboardState.total_leads,  "users",      PRIMARY),
            stat_card("New Leads",     DashboardState.new_leads,    "user_plus",  INFO),
            stat_card("Emails Sent",   DashboardState.emails_sent,  "mail",       WARNING),
            stat_card("Replies",       DashboardState.replies,      "reply",      SUCCESS),
            columns="4",
            spacing="5",
            width="100%",
        ),

        # ── Middle row: Pipeline stages | Industry breakdown ──────────────────
        rx.grid(
            # Pipeline stages
            info_card(
                "Pipeline Stages",
                rx.vstack(
                    rx.foreach(DashboardState.stage_summary, stage_row),
                    spacing="3",
                    width="100%",
                ),
            ),
            # Leads by industry
            info_card(
                "Leads by Industry",
                rx.vstack(
                    rx.foreach(DashboardState.industry_data, industry_row),
                    spacing="3",
                    width="100%",
                ),
            ),
            columns="2",
            spacing="5",
            width="100%",
        ),

        # ── Recent runs ────────────────────────────────────────────────────────
        info_card(
            "Recent Pipeline Runs",
            rx.cond(
                DashboardState.recent_runs.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Run Time"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Leads Found"),
                            rx.table.column_header_cell("Mode"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(DashboardState.recent_runs, run_row)
                    ),
                    width="100%",
                ),
                rx.center(
                    rx.text("No pipeline runs yet. Start Lead Generator to begin.", size="2", color="#6b7280"),
                    padding="20px",
                ),
            ),
        ),

        spacing="6",
        width="100%",
    )


@rx.page(
    route="/dashboard",
    on_load=[AuthState.check_auth, DashboardState.load_dashboard],
)
def dashboard():
    return layout(
        dashboard_content(),
        title="Dashboard",
        subtitle="LeadForge AI overview",
    )
