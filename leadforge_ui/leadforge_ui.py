"""
LeadForge AI — Reflex Frontend Application
==========================================
Entry point for the Reflex app.
Run with:   reflex run
Production: reflex export --no-zip && reflex deploy  (or use serve)
"""

import reflex as rx

# ── Import all pages to register them with the @rx.page decorator ─────────────
from leadforge_ui.pages import (
    login,
    register,
    dashboard,
    leads,
    campaigns,
    masters,
    analytics,
    settings_page,
    lead_generator,
)

# ── App instance ───────────────────────────────────────────────────────────────
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="violet",
        panel_background="solid",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
    ],
    style={
        "font_family": "Inter, system-ui, -apple-system, sans-serif",
        "* ": {"box_sizing": "border-box"},
    },
)
