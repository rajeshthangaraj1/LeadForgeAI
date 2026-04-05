import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.components.cards import info_card
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.settings_state import SettingsState
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER, CARD_STYLE


# ─────────────────────────────────────────────────────────────────────────────
# Gmail Section
# ─────────────────────────────────────────────────────────────────────────────

def gmail_section() -> rx.Component:
    return rx.form(
        rx.box(
            rx.vstack(
                rx.heading("Gmail Configuration", size="4", weight="bold"),
                rx.text(
                    "Use a Gmail account with an App Password (not your main password). "
                    "Enable 2FA → Google Account → App Passwords.",
                    size="2",
                    color="#6b7280",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Gmail Address *", size="2", weight="medium"),
                        rx.input(name="gmail_email", default_value=SettingsState.gmail_email,
                                 placeholder="you@gmail.com", size="2", type="email"),
                        spacing="1", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("App Password *", size="2", weight="medium"),
                        rx.input(name="gmail_password", default_value=SettingsState.gmail_password,
                                 placeholder="xxxx xxxx xxxx xxxx", size="2", type="password"),
                        spacing="1", align_items="start",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("save", size=16),
                        "Save Gmail Settings",
                        type="submit",
                        size="2",
                        style={"background_color": PRIMARY, "color": "white"},
                    ),
                    rx.button(
                        rx.icon("send", size=16),
                        "Test Connection",
                        on_click=SettingsState.test_gmail,
                        variant="soft",
                        size="2",
                    ),
                    spacing="3",
                ),
                rx.cond(
                    SettingsState.gmail_test_result != "",
                    rx.callout(
                        SettingsState.gmail_test_result,
                        icon=rx.cond(SettingsState.gmail_test_ok, "circle_check", "circle_alert"),
                        color_scheme=rx.cond(SettingsState.gmail_test_ok, "green", "red"),
                        variant="soft",
                        size="2",
                    ),
                    rx.box(),
                ),
                spacing="5",
                align_items="start",
                width="100%",
            ),
            style=CARD_STYLE,
        ),
        on_submit=SettingsState.save_gmail,
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Search Providers Section
# ─────────────────────────────────────────────────────────────────────────────

def provider_row(p) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(p["display_name"], size="3", weight="medium"),
                    rx.badge(
                        p["provider_type"].upper(),
                        color_scheme=rx.cond(p["provider_type"] == "free", "green", "orange"),
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(rx.cond(p["description"], p["description"], ""), size="2", color="#6b7280"),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.switch(
                    checked=p["is_enabled"] == 1,
                    on_change=lambda v: SettingsState.toggle_provider(p["id"], v),
                    color_scheme="violet",
                ),
                rx.cond(
                    p["provider_type"] == "paid",
                    rx.hstack(
                        rx.input(
                            placeholder="API Key",
                            default_value=rx.cond(p["api_key"], p["api_key"], ""),
                            size="1",
                            type="password",
                            width="200px",
                            on_blur=lambda v: SettingsState.save_provider_key(p["id"], v),
                        ),
                    ),
                    rx.box(),
                ),
                spacing="2",
                align_items="end",
            ),
            align="center",
            width="100%",
        ),
        padding="16px",
        border_radius="8px",
        border=f"1px solid {BORDER}",
        background_color="white",
    )


def providers_section() -> rx.Component:
    return rx.vstack(
        rx.heading("Search Providers", size="4", weight="bold"),
        rx.text("Enable providers to use during lead generation.", size="2", color="#6b7280"),
        rx.vstack(
            rx.foreach(SettingsState.providers, provider_row),
            spacing="3",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Model Settings Section
# ─────────────────────────────────────────────────────────────────────────────

def model_section() -> rx.Component:
    return rx.form(
        rx.box(
            rx.vstack(
                rx.heading("LLM Model Settings", size="4", weight="bold"),
                rx.text(
                    "Ollama must be running locally. Changes take effect immediately for new pipeline runs.",
                    size="2",
                    color="#6b7280",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Ollama URL", size="2", weight="medium"),
                        rx.input(name="ollama_url", default_value=SettingsState.ollama_url,
                                 placeholder="http://localhost:11434", size="2"),
                        spacing="1", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Model Name", size="2", weight="medium"),
                        rx.input(name="model_name", default_value=SettingsState.model_name,
                                 placeholder="qwen3:8b", size="2"),
                        spacing="1", align_items="start",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                rx.callout(
                    "Tested models: qwen3:8b, mistral-small3.2, llama3.2, gemma3, phi4, deepseek-r1",
                    icon="info",
                    color_scheme="blue",
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    rx.icon("save", size=16),
                    "Save Model Settings",
                    type="submit",
                    size="2",
                    style={"background_color": PRIMARY, "color": "white"},
                ),
                spacing="5",
                align_items="start",
                width="100%",
            ),
            style=CARD_STYLE,
        ),
        on_submit=SettingsState.save_model_settings,
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Settings Page
# ─────────────────────────────────────────────────────────────────────────────

def settings_content() -> rx.Component:
    return rx.vstack(
        gmail_section(),
        rx.box(
            providers_section(),
            style=CARD_STYLE,
        ),
        model_section(),
        spacing="6",
        width="100%",
    )


@rx.page(
    route="/settings",
    on_load=[AuthState.check_auth, SettingsState.load_settings],
)
def settings_page():
    return layout(
        settings_content(),
        title="Settings",
        subtitle="Gmail, search providers, and model configuration",
    )
