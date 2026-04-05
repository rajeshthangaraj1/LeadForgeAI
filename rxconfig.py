import reflex as rx

config = rx.Config(
    app_name="leadforge_ui",
    telemetry_enabled=False,
    plugins=[rx.plugins.SitemapPlugin()],
)
