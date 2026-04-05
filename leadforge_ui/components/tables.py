import reflex as rx
from leadforge_ui.styles.theme import TH_STYLE, TD_STYLE, BORDER, SURFACE, STAGE_COLORS, TEXT_SECONDARY


# ── Stage badge ───────────────────────────────────────────────────────────────

def stage_badge(stage: rx.Var) -> rx.Component:
    """Render a color-coded badge for a lead pipeline stage."""
    return rx.match(
        stage.lower(),
        ("new",       rx.badge("New",       color_scheme="blue",   variant="soft")),
        ("contacted", rx.badge("Contacted", color_scheme="orange", variant="soft")),
        ("replied",   rx.badge("Replied",   color_scheme="cyan",   variant="soft")),
        ("qualified", rx.badge("Qualified", color_scheme="violet", variant="soft")),
        ("won",       rx.badge("Won",       color_scheme="green",  variant="soft")),
        ("lost",      rx.badge("Lost",      color_scheme="red",    variant="soft")),
        rx.badge(stage, color_scheme="gray", variant="soft"),
    )


# ── Email status badge ────────────────────────────────────────────────────────

def email_status_badge(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        ("sent",       rx.badge("Sent",       color_scheme="blue",  variant="soft")),
        ("replied",    rx.badge("Replied",    color_scheme="green", variant="soft")),
        ("auto_reply", rx.badge("Auto Reply", color_scheme="gray",  variant="soft")),
        ("failed",     rx.badge("Failed",     color_scheme="red",   variant="soft")),
        rx.badge("—", color_scheme="gray", variant="soft"),
    )


# ── Generic empty state ───────────────────────────────────────────────────────

def empty_state(message: str = "No records found.", icon: str = "inbox") -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=40, color=TEXT_SECONDARY),
            rx.text(message, size="3", color=TEXT_SECONDARY),
            spacing="3",
            align="center",
        ),
        padding="60px",
        width="100%",
    )


# ── Table wrapper ─────────────────────────────────────────────────────────────

def table_wrapper(
    header_cells: list[str],
    body_rows: rx.Component,
    loading: bool = False,
) -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[
                        rx.table.column_header_cell(
                            rx.text(h, size="1", weight="bold", color=TEXT_SECONDARY),
                            style=TH_STYLE,
                        )
                        for h in header_cells
                    ]
                )
            ),
            rx.table.body(body_rows),
            width="100%",
            style={"border_collapse": "collapse"},
        ),
        background_color="white",
        border_radius="12px",
        border=f"1px solid {BORDER}",
        overflow="hidden",
        width="100%",
    )
