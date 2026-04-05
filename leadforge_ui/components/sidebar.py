import reflex as rx
from leadforge_ui.styles.theme import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHTER, SIDEBAR_STYLE, SIDEBAR_WIDTH,
)
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.base_state import AppState


# ── Navigation items ──────────────────────────────────────────────────────────
_NAV = [
    ("/dashboard",      "layout_dashboard",  "Dashboard"),
    ("/lead-generator", "zap",               "Lead Generator"),
    ("/leads",          "users",             "Leads"),
    ("/campaigns",      "mail",              "Campaigns"),
    ("/masters",        "database",          "Masters"),
    ("/analytics",      "bar_chart_2",       "Analytics"),
    ("/settings",       "settings",          "Settings"),
]


def _nav_item(href: str, icon: str, label: str) -> rx.Component:
    is_active = AppState.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(label, size="2"),
            align="center",
            spacing="3",
        ),
        href=href,
        style=rx.cond(
            is_active,
            {
                "display": "flex",
                "align_items": "center",
                "gap": "12px",
                "padding": "10px 16px",
                "border_radius": "8px",
                "background_color": "rgba(255,255,255,0.18)",
                "color": "white",
                "font_size": "14px",
                "font_weight": "500",
                "text_decoration": "none",
                "width": "100%",
            },
            {
                "display": "flex",
                "align_items": "center",
                "gap": "12px",
                "padding": "10px 16px",
                "border_radius": "8px",
                "color": PRIMARY_LIGHTER,
                "font_size": "14px",
                "font_weight": "500",
                "text_decoration": "none",
                "width": "100%",
                "_hover": {"background_color": "rgba(255,255,255,0.12)", "color": "white"},
            },
        ),
        width="100%",
    )


def sidebar() -> rx.Component:
    return rx.box(
        # ── Logo / brand ─────────────────────────────────────────────────────
        rx.hstack(
            rx.box(
                rx.icon("zap", size=20, color="white"),
                background_color="rgba(255,255,255,0.2)",
                padding="8px",
                border_radius="10px",
            ),
            rx.vstack(
                rx.text("LeadForge AI", color="white", weight="bold", size="3"),
                rx.text("Sales Intelligence", color=PRIMARY_LIGHTER, size="1"),
                spacing="0",
                align_items="start",
            ),
            align="center",
            spacing="3",
            padding="20px 16px 24px",
        ),

        # ── Divider ──────────────────────────────────────────────────────────
        rx.divider(color_scheme="violet", opacity="0.3", margin_x="16px", margin_bottom="8px"),

        # ── Nav items ─────────────────────────────────────────────────────────
        rx.vstack(
            *[_nav_item(href, icon, label) for href, icon, label in _NAV],
            spacing="1",
            padding="4px 12px",
            width="100%",
        ),

        # ── Spacer ────────────────────────────────────────────────────────────
        rx.spacer(),

        # ── User footer ───────────────────────────────────────────────────────
        rx.box(
            rx.divider(color_scheme="violet", opacity="0.3", margin_bottom="12px"),
            rx.hstack(
                rx.box(
                    rx.icon("user", size=16, color="white"),
                    background_color="rgba(255,255,255,0.2)",
                    padding="8px",
                    border_radius="50%",
                ),
                rx.vstack(
                    rx.text(AuthState.username, color="white", size="2", weight="medium"),
                    rx.text("Administrator", color=PRIMARY_LIGHTER, size="1"),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("log_out", size=14),
                    on_click=AuthState.logout,
                    variant="ghost",
                    color_scheme="gray",
                    style={"color": PRIMARY_LIGHTER, "_hover": {"color": "white"}},
                    title="Logout",
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            padding="0 12px 20px",
        ),

        style=SIDEBAR_STYLE,
        display="flex",
        flex_direction="column",
    )
