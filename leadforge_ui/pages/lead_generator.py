import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.components.cards import info_card
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.lead_generator_state import LeadGeneratorState
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER, CARD_STYLE, SUCCESS, ERROR


# ── Agent progress indicator ──────────────────────────────────────────────────

def agent_step(item) -> rx.Component:
    """Single agent row: icon + name."""
    return rx.hstack(
        rx.match(
            item["status"],
            ("done",    rx.icon("circle_check", size=16, color=SUCCESS)),
            ("running", rx.spinner(size="1")),
            rx.icon("circle", size=16, color="#d1d5db"),
        ),
        rx.text(
            item["name"],
            size="2",
            color=rx.cond(
                item["status"] == "pending",
                "#9ca3af",
                rx.cond(item["status"] == "done", "#374151", PRIMARY),
            ),
            weight=rx.cond(item["status"] == "running", "bold", "regular"),
        ),
        align="center",
        spacing="2",
    )


def agent_progress_panel() -> rx.Component:
    return rx.cond(
        LeadGeneratorState.is_running | (LeadGeneratorState.run_result != {}),
        rx.box(
            rx.vstack(
                rx.text("Pipeline Progress", size="2", weight="medium", color="#374151"),
                rx.grid(
                    rx.foreach(LeadGeneratorState.agent_progress, agent_step),
                    columns="3",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            background_color="#f9fafb",
            border_radius="10px",
            border=f"1px solid {BORDER}",
            padding="16px",
        ),
        rx.box(),
    )


# ── Controls card ─────────────────────────────────────────────────────────────

def controls_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Product", size="2", weight="medium", color="#374151"),
                    rx.select(
                        LeadGeneratorState.product_names,
                        value=LeadGeneratorState.selected_product_name,
                        on_change=LeadGeneratorState.set_product_by_name,
                        placeholder="Select product",
                        size="2",
                        width="220px",
                        disabled=LeadGeneratorState.is_running,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.vstack(
                    rx.text("Run Mode", size="2", weight="medium", color="#374151"),
                    rx.radio_group(
                        ["start", "rerun"],
                        default_value="start",
                        on_change=LeadGeneratorState.set_run_mode,
                        direction="row",
                        disabled=LeadGeneratorState.is_running,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(" ", size="2"),
                    rx.cond(
                        LeadGeneratorState.is_running,
                        rx.button(
                            rx.icon("square", size=16),
                            "Stop Pipeline",
                            on_click=LeadGeneratorState.stop_pipeline,
                            color_scheme="red",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("zap", size=16),
                            "Start Pipeline",
                            on_click=LeadGeneratorState.start_pipeline,
                            size="2",
                            style={"background_color": PRIMARY, "color": "white"},
                        ),
                    ),
                    spacing="1",
                    align_items="start",
                ),
                align="end",
                spacing="6",
                flex_wrap="wrap",
                width="100%",
            ),

            # ── Mode description ──────────────────────────────────────────────
            rx.match(
                LeadGeneratorState.run_mode,
                ("start",
                    rx.callout(
                        "Start Mode: Clears existing leads for the product and runs a full fresh pipeline.",
                        icon="info",
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                    ),
                ),
                ("rerun",
                    rx.callout(
                        "Rerun Mode: Keeps existing leads and appends new ones (deduplication by email).",
                        icon="info",
                        color_scheme="violet",
                        variant="soft",
                        size="2",
                    ),
                ),
                rx.box(),
            ),

            # ── Running indicator ─────────────────────────────────────────────
            rx.cond(
                LeadGeneratorState.is_running,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Pipeline running…", size="2", weight="medium", color=PRIMARY),
                    spacing="2",
                    align="center",
                    padding="10px 16px",
                    background_color="#f5f3ff",
                    border_radius="8px",
                    border=f"1px solid #c4b5fd",
                ),
                rx.box(),
            ),

            agent_progress_panel(),

            spacing="4",
            align_items="start",
            width="100%",
        ),
        style=CARD_STYLE,
    )


# ── Live log viewer ───────────────────────────────────────────────────────────

def log_line(msg: str) -> rx.Component:
    return rx.text(
        msg,
        size="1",
        color="#d4d4d8",
        font_family="'JetBrains Mono', 'Fira Code', monospace",
        white_space="pre-wrap",
        width="100%",
    )


def log_viewer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("terminal", size=16, color="#a1a1aa"),
                rx.text("Agent Logs", size="2", weight="medium", color="#a1a1aa"),
                rx.spacer(),
                rx.cond(
                    LeadGeneratorState.is_running,
                    rx.badge("LIVE", color_scheme="green", variant="soft", size="1"),
                    rx.cond(
                        LeadGeneratorState.run_logs.length() > 0,
                        rx.badge("DONE", color_scheme="violet", variant="soft", size="1"),
                        rx.badge("IDLE", color_scheme="gray", variant="soft", size="1"),
                    ),
                ),
                rx.cond(
                    LeadGeneratorState.run_logs.length() > 0,
                    rx.icon_button(
                        rx.icon("trash-2", size=13),
                        size="1",
                        variant="ghost",
                        color_scheme="red",
                        on_click=LeadGeneratorState.clear_logs,
                        title="Clear all logs",
                    ),
                    rx.box(),
                ),
                spacing="2",
                align="center",
                padding="12px 16px",
                border_bottom="1px solid #27272a",
            ),
            rx.box(
                rx.cond(
                    LeadGeneratorState.run_logs.length() > 0,
                    rx.vstack(
                        rx.foreach(LeadGeneratorState.run_logs, log_line),
                        spacing="1",
                        width="100%",
                        align_items="start",
                    ),
                    rx.center(
                        rx.text(
                            "Logs will appear here when the pipeline is running…",
                            size="2",
                            color="#52525b",
                        ),
                        padding="40px",
                    ),
                ),
                padding="16px",
                overflow_y="auto",
                max_height="420px",
                width="100%",
            ),
        ),
        background_color="#18181b",
        border_radius="12px",
        border="1px solid #27272a",
        overflow="hidden",
        width="100%",
    )


# ── Run summary card ──────────────────────────────────────────────────────────

def run_summary() -> rx.Component:
    return rx.cond(
        LeadGeneratorState.run_result != {},
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("circle_check_big", size=20, color=SUCCESS),
                    rx.text("Pipeline Complete", size="3", weight="bold", color="#111827"),
                    spacing="2",
                    align="center",
                ),
                rx.foreach(
                    LeadGeneratorState.run_summary_lines,
                    lambda line: rx.text(line, size="2", color="#374151"),
                ),
                spacing="3",
                align_items="start",
            ),
            style={**CARD_STYLE, "border_color": "#bbf7d0", "background_color": "#f0fdf4"},
        ),
        rx.box(),
    )


# ── Error banner ──────────────────────────────────────────────────────────────

def error_banner() -> rx.Component:
    return rx.cond(
        LeadGeneratorState.run_error != "",
        rx.callout(
            LeadGeneratorState.run_error,
            icon="circle_alert",
            color_scheme="red",
            variant="soft",
        ),
        rx.box(),
    )


# ── Delete run confirm dialog ─────────────────────────────────────────────────

def delete_run_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Pipeline Run"),
            rx.alert_dialog.description(
                "This will permanently delete the run record, all agent logs, and the leads generated by this run.",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Cancel", variant="soft", color_scheme="gray",
                              on_click=LeadGeneratorState.cancel_delete_run),
                ),
                rx.alert_dialog.action(
                    rx.button("Delete", color_scheme="red",
                              on_click=LeadGeneratorState.confirm_delete_run),
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
            ),
        ),
        open=LeadGeneratorState.show_delete_run_confirm,
        on_open_change=LeadGeneratorState.set_show_delete_run_confirm,
    )


# ── Recent runs table ─────────────────────────────────────────────────────────

def recent_run_row(run) -> rx.Component:
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
        rx.table.cell(
            rx.text(rx.cond(run["notes"], run["notes"][:60], "—"), size="1", color="#6b7280"),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash_2", size=14),
                on_click=LeadGeneratorState.open_delete_run_confirm(run["id"]),
                variant="ghost",
                size="1",
                color_scheme="red",
                title="Delete run",
                disabled=LeadGeneratorState.is_running,
            ),
        ),
        _hover={"background_color": "#fafafa"},
    )


# ── Page content ──────────────────────────────────────────────────────────────

def lead_generator_content() -> rx.Component:
    return rx.vstack(
        controls_card(),
        error_banner(),
        run_summary(),
        log_viewer(),
        info_card(
            "Recent Pipeline Runs",
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Run Time", "Status", "Leads Found", "Mode", "Summary", ""]],
                    )
                ),
                rx.table.body(
                    rx.foreach(LeadGeneratorState.recent_runs, recent_run_row)
                ),
                width="100%",
            ),
        ),
        delete_run_dialog(),
        spacing="6",
        width="100%",
    )


@rx.page(
    route="/lead-generator",
    on_load=[AuthState.check_auth, LeadGeneratorState.load_page],
)
def lead_generator():
    return layout(
        lead_generator_content(),
        title="Lead Generator",
        subtitle="Run the AI pipeline to discover and enrich leads",
    )
