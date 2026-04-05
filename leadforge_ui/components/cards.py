import reflex as rx
from leadforge_ui.styles.theme import CARD_STYLE, TEXT_SECONDARY, PRIMARY


# ── Stat card (KPI) ───────────────────────────────────────────────────────────

def stat_card(
    title: str,
    value,
    icon: str,
    icon_color: str = PRIMARY,
    delta: str = "",
    delta_positive: bool = True,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(title, size="2", color=TEXT_SECONDARY, weight="medium"),
                    rx.heading(value, size="7", weight="bold", color="#111827"),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.box(
                    rx.icon(icon, size=22, color=icon_color),
                    background_color=f"{icon_color}18",
                    padding="12px",
                    border_radius="12px",
                ),
                align="start",
                width="100%",
            ),
            rx.cond(
                delta != "",
                rx.hstack(
                    rx.icon(
                        rx.cond(delta_positive, "trending_up", "trending_down"),
                        size=14,
                        color=rx.cond(delta_positive, "#10b981", "#ef4444"),
                    ),
                    rx.text(
                        delta,
                        size="1",
                        color=rx.cond(delta_positive, "#10b981", "#ef4444"),
                        weight="medium",
                    ),
                    align="center",
                    spacing="1",
                ),
                rx.box(),
            ),
            spacing="3",
            align_items="start",
        ),
        style=CARD_STYLE,
    )


# ── Info / content card ────────────────────────────────────────────────────────

def info_card(title: str, content: rx.Component, extra: rx.Component = None) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(title, size="3", weight="bold", color="#111827"),
                rx.spacer(),
                extra or rx.box(),
                align="center",
                width="100%",
            ),
            rx.divider(margin_y="4px"),
            content,
            spacing="3",
            align_items="start",
            width="100%",
        ),
        style=CARD_STYLE,
    )
