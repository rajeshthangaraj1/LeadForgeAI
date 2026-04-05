import reflex as rx
from leadforge_ui.styles.theme import CONTENT_STYLE
from leadforge_ui.components.sidebar import sidebar
from leadforge_ui.components.header import header
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.base_state import AppState


def layout(
    content: rx.Component,
    title: str = "",
    subtitle: str = "",
) -> rx.Component:
    """
    Main page layout: fixed sidebar on left, header + content on right.
    Redirects to /login if not authenticated.
    """
    return rx.cond(
        AuthState.is_authenticated,
        rx.box(
            sidebar(),
            rx.box(
                header(title=title, subtitle=subtitle),
                rx.box(
                    content,
                    padding="28px",
                    flex="1",
                ),
                style=CONTENT_STYLE,
                flex="1",
            ),
            display="flex",
            min_height="100vh",
            font_family="Inter, system-ui, sans-serif",
        ),
        rx.center(
            rx.spinner(size="3"),
            min_height="100vh",
        ),
    )
