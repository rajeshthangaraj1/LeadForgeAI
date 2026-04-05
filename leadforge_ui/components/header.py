import reflex as rx
from leadforge_ui.styles.theme import HEADER_STYLE, PRIMARY, TEXT_SECONDARY, BORDER
from leadforge_ui.state.base_state import AppState


def header(title: str = "", subtitle: str = "") -> rx.Component:
    return rx.box(
        rx.hstack(
            # ── Page title ────────────────────────────────────────────────────
            rx.vstack(
                rx.heading(title, size="5", weight="bold", color="#111827"),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, size="2", color=TEXT_SECONDARY),
                    rx.box(),
                ),
                spacing="0",
                align_items="start",
            ),

            rx.spacer(),

            # ── Product selector ─────────────────────────────────────────────
            rx.cond(
                AppState.products.length() > 0,
                rx.hstack(
                    rx.icon("package", size=16, color=TEXT_SECONDARY),
                    rx.select(
                        AppState.product_labels,
                        value=AppState.selected_product_name,
                        on_change=AppState.set_product,
                        size="2",
                        variant="soft",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.box(),
            ),

            align="center",
            width="100%",
        ),
        style=HEADER_STYLE,
    )
