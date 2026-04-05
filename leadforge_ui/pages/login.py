import reflex as rx
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, PRIMARY_LIGHTER, BORDER
from leadforge_ui.state.auth import AuthState


def login_page() -> rx.Component:
    return rx.box(
        # ── Background gradient ───────────────────────────────────────────────
        rx.box(
            rx.center(
                rx.vstack(
                    # ── Brand ─────────────────────────────────────────────────
                    rx.vstack(
                        rx.hstack(
                            rx.box(
                                rx.icon("zap", size=28, color="white"),
                                background_color=PRIMARY,
                                padding="14px",
                                border_radius="16px",
                            ),
                            align="center",
                        ),
                        rx.heading("LeadForge AI", size="7", weight="bold", color="#111827"),
                        rx.text(
                            "AI-powered B2B lead generation platform",
                            size="3",
                            color="#6b7280",
                        ),
                        spacing="3",
                        align="center",
                    ),

                    # ── Card ──────────────────────────────────────────────────
                    rx.box(
                        rx.vstack(
                            rx.heading("Sign in", size="5", weight="bold", color="#111827"),
                            rx.text("Enter your credentials to continue", size="2", color="#6b7280"),
                            rx.spacer(height="8px"),

                            rx.form(
                                rx.vstack(
                                    # Error
                                    rx.cond(
                                        AuthState.login_error != "",
                                        rx.callout(
                                            AuthState.login_error,
                                            icon="circle_alert",
                                            color_scheme="red",
                                            variant="soft",
                                            size="2",
                                        ),
                                        rx.box(),
                                    ),

                                    # Username
                                    rx.vstack(
                                        rx.text("Username", size="2", weight="medium", color="#374151"),
                                        rx.input(
                                            name="username",
                                            placeholder="Enter username",
                                            size="3",
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                        align_items="start",
                                    ),

                                    # Password
                                    rx.vstack(
                                        rx.text("Password", size="2", weight="medium", color="#374151"),
                                        rx.input(
                                            name="password",
                                            type="password",
                                            placeholder="Enter password",
                                            size="3",
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                        align_items="start",
                                    ),

                                    # Submit
                                    rx.button(
                                        rx.hstack(
                                            rx.icon("log_in", size=16),
                                            rx.text("Sign In"),
                                            spacing="2",
                                            align="center",
                                        ),
                                        type="submit",
                                        size="3",
                                        width="100%",
                                        style={
                                            "background_color": PRIMARY,
                                            "color": "white",
                                            "_hover": {"background_color": PRIMARY_DARK},
                                        },
                                    ),

                                    spacing="4",
                                    width="100%",
                                ),
                                on_submit=AuthState.login,
                                width="100%",
                            ),

                            spacing="2",
                            align_items="start",
                            width="100%",
                        ),
                        background_color="white",
                        padding="40px",
                        border_radius="16px",
                        box_shadow="0 4px 24px rgba(0,0,0,0.1)",
                        border=f"1px solid {BORDER}",
                        width="400px",
                    ),

                    # ── Register link ─────────────────────────────────────────
                    rx.hstack(
                        rx.text("Don't have an account?", size="2", color="#6b7280"),
                        rx.link(
                            "Create account",
                            href="/register",
                            size="2",
                            style={"color": PRIMARY, "font_weight": "600"},
                        ),
                        spacing="2",
                        justify="center",
                    ),

                    # ── Footer ────────────────────────────────────────────────
                    rx.text(
                        "LeadForge AI — Internal SaaS Tool",
                        size="1",
                        color="#9ca3af",
                    ),

                    spacing="6",
                    align="center",
                    width="100%",
                ),
                min_height="100vh",
                padding="40px 20px",
            ),
            background_color="#f3f4f6",
            min_height="100vh",
        ),
    )


@rx.page(route="/login")
def login():
    return login_page()


@rx.page(route="/", on_load=AuthState.redirect_from_index)
def index():
    return rx.center(rx.spinner(size="3"), min_height="100vh")
