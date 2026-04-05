import reflex as rx
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER
from leadforge_ui.state.auth import AuthState


def register_page() -> rx.Component:
    return rx.box(
        rx.center(
            rx.vstack(
                # ── Brand ─────────────────────────────────────────────────────
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
                    rx.text("Create your account", size="3", color="#6b7280"),
                    spacing="3",
                    align="center",
                ),

                # ── Card ──────────────────────────────────────────────────────
                rx.box(
                    rx.vstack(
                        rx.heading("Sign up", size="5", weight="bold", color="#111827"),
                        rx.text(
                            "Fill in your details to create a new account.",
                            size="2",
                            color="#6b7280",
                        ),
                        rx.spacer(height="8px"),

                        rx.form(
                            rx.vstack(
                                # Success
                                rx.cond(
                                    AuthState.register_success != "",
                                    rx.callout(
                                        AuthState.register_success,
                                        icon="circle_check",
                                        color_scheme="green",
                                        variant="soft",
                                        size="2",
                                    ),
                                    rx.box(),
                                ),
                                # Error
                                rx.cond(
                                    AuthState.register_error != "",
                                    rx.callout(
                                        AuthState.register_error,
                                        icon="circle_alert",
                                        color_scheme="red",
                                        variant="soft",
                                        size="2",
                                    ),
                                    rx.box(),
                                ),

                                # Full Name
                                rx.vstack(
                                    rx.text("Full Name", size="2", weight="medium", color="#374151"),
                                    rx.input(
                                        name="full_name",
                                        placeholder="Your full name",
                                        size="3",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                    align_items="start",
                                ),

                                # Email
                                rx.vstack(
                                    rx.text("Email Address", size="2", weight="medium", color="#374151"),
                                    rx.input(
                                        name="email",
                                        type="email",
                                        placeholder="you@company.com",
                                        size="3",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                    align_items="start",
                                ),

                                # Username
                                rx.vstack(
                                    rx.text("Username *", size="2", weight="medium", color="#374151"),
                                    rx.input(
                                        name="username",
                                        placeholder="Choose a username",
                                        size="3",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                    align_items="start",
                                ),

                                # Password
                                rx.vstack(
                                    rx.text("Password *", size="2", weight="medium", color="#374151"),
                                    rx.input(
                                        name="password",
                                        type="password",
                                        placeholder="Min. 6 characters",
                                        size="3",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                    align_items="start",
                                ),

                                # Confirm Password
                                rx.vstack(
                                    rx.text("Confirm Password *", size="2", weight="medium", color="#374151"),
                                    rx.input(
                                        name="confirm_password",
                                        type="password",
                                        placeholder="Repeat password",
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
                                        rx.icon("user_plus", size=16),
                                        rx.text("Create Account"),
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
                            on_submit=AuthState.register,
                            width="100%",
                        ),

                        # ── Already have account ───────────────────────────────
                        rx.hstack(
                            rx.text("Already have an account?", size="2", color="#6b7280"),
                            rx.link("Sign in", href="/login", size="2",
                                    style={"color": PRIMARY, "font_weight": "600"}),
                            spacing="2",
                            justify="center",
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
                    width="440px",
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
    )


@rx.page(route="/register")
def register():
    return register_page()
