# ── LeadForge AI — Design tokens (based on Google Stitch designs) ─────────────

# ── Color palette ──────────────────────────────────────────────────────────────
PRIMARY         = "#5e5696"
PRIMARY_DARK    = "#4a4278"
PRIMARY_LIGHT   = "#c1b7ff"
PRIMARY_LIGHTER = "#e5deff"
ACCENT          = "#e2e900"
ACCENT_DARK     = "#5f6200"
SURFACE         = "#f9f9f9"
SURFACE_CARD    = "#ffffff"
BORDER          = "#e5e7eb"
BORDER_LIGHT    = "#f0f0f0"
TEXT_PRIMARY    = "#111827"
TEXT_SECONDARY  = "#6b7280"
TEXT_MUTED      = "#9ca3af"
SUCCESS         = "#10b981"
WARNING         = "#f59e0b"
ERROR           = "#ef4444"
INFO            = "#3b82f6"

# ── Stage badge color mapping (Radix color_scheme names) ──────────────────────
STAGE_COLORS: dict[str, str] = {
    "new":       "blue",
    "contacted": "orange",
    "replied":   "cyan",
    "qualified": "purple",
    "won":       "green",
    "lost":      "red",
}

STAGE_LABELS: list[str] = ["New", "Contacted", "Replied", "Qualified", "Won", "Lost"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
SIDEBAR_WIDTH = "260px"

SIDEBAR_STYLE: dict = {
    "position": "fixed",
    "left": "0",
    "top": "0",
    "width": SIDEBAR_WIDTH,
    "height": "100vh",
    "background_color": PRIMARY,
    "z_index": "100",
    "overflow_y": "auto",
    "display": "flex",
    "flex_direction": "column",
}

CONTENT_STYLE: dict = {
    "margin_left": SIDEBAR_WIDTH,
    "min_height": "100vh",
    "background_color": SURFACE,
    "display": "flex",
    "flex_direction": "column",
}

# ── Card ──────────────────────────────────────────────────────────────────────
CARD_STYLE: dict = {
    "background_color": SURFACE_CARD,
    "border_radius": "12px",
    "box_shadow": "0 1px 4px rgba(0,0,0,0.07)",
    "padding": "24px",
    "border": f"1px solid {BORDER}",
}

# ── Header ────────────────────────────────────────────────────────────────────
HEADER_STYLE: dict = {
    "background_color": SURFACE_CARD,
    "border_bottom": f"1px solid {BORDER}",
    "padding": "0 28px",
    "height": "64px",
    "display": "flex",
    "align_items": "center",
    "justify_content": "space-between",
    "position": "sticky",
    "top": "0",
    "z_index": "50",
}

# ── Nav item ──────────────────────────────────────────────────────────────────
NAV_ITEM_STYLE: dict = {
    "display": "flex",
    "align_items": "center",
    "gap": "12px",
    "padding": "10px 20px",
    "border_radius": "8px",
    "color": PRIMARY_LIGHTER,
    "font_size": "14px",
    "font_weight": "500",
    "cursor": "pointer",
    "transition": "all 0.15s",
    "text_decoration": "none",
    "width": "100%",
    "_hover": {"background_color": "rgba(255,255,255,0.12)", "color": "white"},
}

NAV_ITEM_ACTIVE_STYLE: dict = {
    **NAV_ITEM_STYLE,
    "background_color": "rgba(255,255,255,0.18)",
    "color": "white",
    "_hover": {"background_color": "rgba(255,255,255,0.22)", "color": "white"},
}

# ── Buttons ───────────────────────────────────────────────────────────────────
BTN_PRIMARY: dict = {
    "background_color": PRIMARY,
    "color": "white",
    "border_radius": "8px",
    "font_weight": "600",
    "cursor": "pointer",
    "_hover": {"background_color": PRIMARY_DARK},
}

# ── Table ─────────────────────────────────────────────────────────────────────
TH_STYLE: dict = {
    "background_color": SURFACE,
    "font_weight": "600",
    "font_size": "12px",
    "text_transform": "uppercase",
    "letter_spacing": "0.05em",
    "color": TEXT_SECONDARY,
    "padding": "12px 16px",
    "border_bottom": f"2px solid {BORDER}",
}

TD_STYLE: dict = {
    "padding": "14px 16px",
    "border_bottom": f"1px solid {BORDER_LIGHT}",
    "font_size": "14px",
    "color": TEXT_PRIMARY,
    "vertical_align": "middle",
}

# ── Input ─────────────────────────────────────────────────────────────────────
INPUT_STYLE: dict = {
    "border": f"1px solid {BORDER}",
    "border_radius": "8px",
    "padding": "10px 14px",
    "font_size": "14px",
    "width": "100%",
    "_focus": {"border_color": PRIMARY, "outline": "none", "box_shadow": f"0 0 0 3px {PRIMARY_LIGHTER}"},
}
