import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.base_state import AppState
from leadforge_ui.state.masters_state import MastersState
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER, TD_STYLE, CARD_STYLE


# ─────────────────────────────────────────────────────────────────────────────
# Company Profile Tab
# ─────────────────────────────────────────────────────────────────────────────

def company_profile_tab() -> rx.Component:
    return rx.form(
        rx.box(
            rx.vstack(
                rx.grid(
                    rx.vstack(
                        rx.text("Company Name *", size="2", weight="medium"),
                        rx.input(name="company_name", default_value=MastersState.cp_company_name,
                                 placeholder="Acme Corp", size="2"),
                        spacing="1", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Industry", size="2", weight="medium"),
                        rx.input(name="industry", default_value=MastersState.cp_industry,
                                 placeholder="e.g. SaaS / Consulting", size="2"),
                        spacing="1", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Website", size="2", weight="medium"),
                        rx.input(name="website", default_value=MastersState.cp_website,
                                 placeholder="https://yourcompany.com", size="2"),
                        spacing="1", align_items="start",
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Company Description", size="2", weight="medium"),
                    rx.text_area(
                        name="description",
                        default_value=MastersState.cp_description,
                        placeholder="What does your company do? What problems do you solve?",
                        rows="4",
                        size="2",
                        width="100%",
                    ),
                    spacing="1", align_items="start", width="100%",
                ),
                rx.button(
                    rx.icon("save", size=16),
                    "Save Company Profile",
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
        on_submit=MastersState.save_company,
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Products Tab
# ─────────────────────────────────────────────────────────────────────────────

def product_row(p) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["product_name"], size="2", weight="medium"), style=TD_STYLE),
        rx.table.cell(
            rx.text(
                rx.cond(p["description"], p["description"][:80], "—"),
                size="2", color="#6b7280",
            ),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.text(rx.cond(p["created_at"], p["created_at"][:10], "—"), size="2"),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=MastersState.open_edit_product(p["id"]),
                    variant="ghost", size="1", color_scheme="violet", title="Edit",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=MastersState.delete_product_confirm(p["id"]),
                    variant="ghost", size="1", color_scheme="red", title="Delete",
                ),
                spacing="1",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


def add_product_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Add Product"),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Product Name *", size="2", weight="medium"),
                        rx.input(name="product_name", placeholder="e.g. LeadForge Pro", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Description", size="2", weight="medium"),
                        rx.text_area(name="description", placeholder="Describe this product…",
                                     rows="3", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=MastersState.close_add_product),
                        ),
                        rx.button("Add Product", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=MastersState.add_product,
                width="100%",
            ),
            max_width="440px", width="100%", padding="24px",
        ),
        open=MastersState.show_add_product_modal,
        on_open_change=MastersState.set_show_add_product_modal,
    )


def edit_product_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Edit Product"),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Product Name *", size="2", weight="medium"),
                        rx.input(name="product_name", default_value=MastersState.prod_name,
                                 size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Description", size="2", weight="medium"),
                        rx.text_area(name="description", default_value=MastersState.prod_description,
                                     rows="3", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=MastersState.close_edit_product),
                        ),
                        rx.button("Save", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=MastersState.save_edit_product,
                width="100%",
            ),
            max_width="440px", width="100%", padding="24px",
        ),
        open=MastersState.show_edit_product_modal,
        on_open_change=MastersState.set_show_edit_product_modal,
    )


def products_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Products", size="3", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Add Product",
                on_click=MastersState.open_add_product,
                size="2",
                style={"background_color": PRIMARY, "color": "white"},
            ),
            align="center",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Product Name", "Description", "Created", "Actions"]],
                    )
                ),
                rx.table.body(rx.foreach(MastersState.products, product_row)),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
        ),
        add_product_modal(),
        edit_product_modal(),
        spacing="4",
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Target Audience Tab
# ─────────────────────────────────────────────────────────────────────────────

def _ta_form_fields() -> rx.Component:
    """Shared form fields used in both Add and Edit TA modals."""
    return rx.vstack(
        rx.grid(
            rx.vstack(
                rx.text("Industry", size="2", weight="medium"),
                rx.input(name="industry", default_value=MastersState.ta_industry,
                         placeholder="e.g. Real Estate, Retail", size="2", width="100%"),
                spacing="1", align_items="start",
            ),
            rx.vstack(
                rx.text("Location", size="2", weight="medium"),
                rx.input(name="location", default_value=MastersState.ta_location,
                         placeholder="e.g. Dubai, UAE", size="2", width="100%"),
                spacing="1", align_items="start",
            ),
            rx.vstack(
                rx.text("Country", size="2", weight="medium"),
                rx.select(
                    ["UAE", "India", "Saudi Arabia", "USA", "UK", "Australia",
                     "Qatar", "Kuwait", "Bahrain", "Oman", "Singapore", "Germany", "Canada"],
                    name="country",
                    default_value=MastersState.ta_country,
                    placeholder="Select country",
                    size="2",
                ),
                spacing="1", align_items="start",
            ),
            rx.vstack(
                rx.text("Business Type", size="2", weight="medium"),
                rx.select(["B2B", "B2C", "Both"], name="business_type",
                          default_value=MastersState.ta_business_type, size="2"),
                spacing="1", align_items="start",
            ),
            rx.vstack(
                rx.text("Target Roles", size="2", weight="medium"),
                rx.input(name="roles", default_value=MastersState.ta_roles,
                         placeholder="e.g. CEO, Manager, Owner", size="2", width="100%"),
                spacing="1", align_items="start",
            ),
            rx.vstack(
                rx.text("Keywords", size="2", weight="medium"),
                rx.input(name="keywords", default_value=MastersState.ta_keywords,
                         placeholder="e.g. ERP, automation", size="2", width="100%"),
                spacing="1", align_items="start",
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.vstack(
            rx.text("Company Size", size="2", weight="medium"),
            rx.flex(
                rx.checkbox("1-10",
                    checked=MastersState.ta_company_sizes.contains("1-10"),
                    on_change=MastersState.toggle_company_size("1-10"),
                ),
                rx.checkbox("11-50",
                    checked=MastersState.ta_company_sizes.contains("11-50"),
                    on_change=MastersState.toggle_company_size("11-50"),
                ),
                rx.checkbox("51-200",
                    checked=MastersState.ta_company_sizes.contains("51-200"),
                    on_change=MastersState.toggle_company_size("51-200"),
                ),
                rx.checkbox("201-500",
                    checked=MastersState.ta_company_sizes.contains("201-500"),
                    on_change=MastersState.toggle_company_size("201-500"),
                ),
                rx.checkbox("501-1000",
                    checked=MastersState.ta_company_sizes.contains("501-1000"),
                    on_change=MastersState.toggle_company_size("501-1000"),
                ),
                rx.checkbox("1000+",
                    checked=MastersState.ta_company_sizes.contains("1000+"),
                    on_change=MastersState.toggle_company_size("1000+"),
                ),
                wrap="wrap", gap="4", width="100%",
            ),
            spacing="1", align_items="start", width="100%",
        ),
        rx.vstack(
            rx.text("Competitors", size="2", weight="medium"),
            rx.input(name="competitors", default_value=MastersState.ta_competitors,
                     placeholder="e.g. Competitor A, Competitor B", size="2", width="100%"),
            spacing="1", align_items="start", width="100%",
        ),
        spacing="4", width="100%",
    )


def add_ta_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Add Target Audience"),
            rx.form(
                rx.vstack(
                    _ta_form_fields(),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=MastersState.close_add_ta_modal),
                        ),
                        rx.button("Add", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=MastersState.add_ta,
                width="100%",
            ),
            max_width="600px", width="100%", padding="24px",
        ),
        open=MastersState.show_add_ta_modal,
        on_open_change=MastersState.set_show_add_ta_modal,
    )


def edit_ta_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Edit Target Audience"),
            rx.form(
                rx.vstack(
                    _ta_form_fields(),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=MastersState.close_edit_ta_modal),
                        ),
                        rx.button("Save", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=MastersState.save_edit_ta,
                width="100%",
            ),
            max_width="600px", width="100%", padding="24px",
        ),
        open=MastersState.show_edit_ta_modal,
        on_open_change=MastersState.set_show_edit_ta_modal,
    )


def ta_row(t) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(rx.cond(t["industry"], t["industry"], "—"), size="2"), style=TD_STYLE),
        rx.table.cell(rx.text(rx.cond(t["country"], t["country"], "—"), size="2"), style=TD_STYLE),
        rx.table.cell(
            rx.badge(t["business_type"],
                     color_scheme=rx.cond(t["business_type"] == "B2B", "blue",
                                          rx.cond(t["business_type"] == "B2C", "green", "gray")),
                     variant="soft", size="1"),
            style=TD_STYLE,
        ),
        rx.table.cell(rx.text(rx.cond(t["roles"], t["roles"], "—"), size="2", color="#6b7280"), style=TD_STYLE),
        rx.table.cell(rx.text(rx.cond(t["company_size"], t["company_size"], "—"), size="2", color="#6b7280"), style=TD_STYLE),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=MastersState.open_edit_ta_modal(t["id"]),
                    variant="ghost", size="1", color_scheme="violet", title="Edit",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=MastersState.delete_ta(t["id"]),
                    variant="ghost", size="1", color_scheme="red", title="Delete",
                ),
                spacing="1",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


def target_audience_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Target Audience for:", size="2", weight="medium", color="#374151"),
            rx.select(
                MastersState.product_names_ta,
                on_change=MastersState.set_ta_product,
                placeholder="Select product",
                size="2",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Add Target Audience",
                on_click=MastersState.open_add_ta_modal,
                size="2",
                style={"background_color": PRIMARY, "color": "white"},
            ),
            align="center",
            width="100%",
            spacing="3",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Industry", "Country", "Type", "Roles", "Company Size", "Actions"]],
                    )
                ),
                rx.table.body(rx.foreach(MastersState.target_audiences, ta_row)),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
        ),
        add_ta_modal(),
        edit_ta_modal(),
        spacing="4",
        width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Email Templates Tab
# ─────────────────────────────────────────────────────────────────────────────

def template_row(t) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(t["name"], size="2", weight="medium"), style=TD_STYLE),
        rx.table.cell(rx.text(t["subject"], size="2"), style=TD_STYLE),
        rx.table.cell(
            rx.text(rx.cond(t["body"], t["body"][:60] + "…", "—"), size="2", color="#6b7280"),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.text(rx.cond(t["created_at"], t["created_at"][:10], "—"), size="2"),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=MastersState.open_edit_template(t["id"]),
                    variant="ghost", size="1", color_scheme="violet",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=MastersState.delete_template_confirm(t["id"]),
                    variant="ghost", size="1", color_scheme="red",
                ),
                spacing="1",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


def _template_modal_form(
    title: str,
    name_val, subject_val, body_val,
    on_submit, open_var, on_open, close_fn,
) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Template Name *", size="2", weight="medium"),
                        rx.input(name="name", default_value=name_val, placeholder="e.g. Cold Outreach", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Email Subject *", size="2", weight="medium"),
                        rx.input(name="subject", default_value=subject_val,
                                 placeholder="e.g. Hi {name}, quick question about {company}", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Email Body *", size="2", weight="medium"),
                        rx.text_area(
                            name="body", default_value=body_val, rows="8", size="2", width="100%",
                            placeholder="Hi {first_name},\n\nI noticed {company} does …\n\nWould you be open to a quick call?\n\nBest,\nYour Name",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Available placeholders", size="1", weight="medium", color="#6b7280"),
                                rx.flex(
                                    *[
                                        rx.box(
                                            rx.hstack(
                                                rx.code(ph, size="1", color_scheme="violet"),
                                                rx.text(desc, size="1", color="#6b7280"),
                                                spacing="2", align="center",
                                            ),
                                        )
                                        for ph, desc in [
                                            ("{name}",       "Full name"),
                                            ("{first_name}", "First name only"),
                                            ("{company}",    "Company name"),
                                            ("{role}",       "Job title / role"),
                                            ("{industry}",   "Industry"),
                                            ("{location}",   "City / location"),
                                            ("{email}",      "Email address"),
                                        ]
                                    ],
                                    wrap="wrap",
                                    gap="3",
                                ),
                                spacing="2",
                            ),
                            padding="10px 14px",
                            background_color="#f9fafb",
                            border="1px solid #e5e7eb",
                            border_radius="8px",
                            width="100%",
                        ),
                        spacing="2", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray", size="2", on_click=close_fn)),
                        rx.button("Save Template", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=on_submit,
                width="100%",
            ),
            max_width="560px", width="100%", padding="24px",
        ),
        open=open_var,
        on_open_change=on_open,
    )


def templates_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Email Templates", size="3", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Add Template",
                on_click=MastersState.open_add_template,
                size="2",
                style={"background_color": PRIMARY, "color": "white"},
            ),
            align="center", width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Name", "Subject", "Preview", "Created", "Actions"]],
                    )
                ),
                rx.table.body(rx.foreach(MastersState.templates, template_row)),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
        ),
        # Add modal
        _template_modal_form(
            "Add Email Template", "", "", "",
            MastersState.add_template,
            MastersState.show_add_template_modal,
            MastersState.set_show_add_template_modal,
            MastersState.close_add_template,
        ),
        # Edit modal
        _template_modal_form(
            "Edit Email Template",
            MastersState.tpl_name,
            MastersState.tpl_subject,
            MastersState.tpl_body,
            MastersState.save_edit_template,
            MastersState.show_edit_template_modal,
            MastersState.set_show_edit_template_modal,
            MastersState.close_edit_template,
        ),
        spacing="4", width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Country Sources Tab
# ─────────────────────────────────────────────────────────────────────────────

def _cs_modal(title, country_val, btype_val, url_val, on_submit, open_var, on_open, close_fn) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Country *", size="2", weight="medium"),
                        rx.select(
                            ["UAE", "India", "Saudi Arabia", "USA", "UK", "Australia",
                             "Qatar", "Kuwait", "Bahrain", "Oman", "Singapore", "Germany", "Canada"],
                            name="country",
                            default_value=country_val,
                            placeholder="Select country",
                            size="2",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Business Type", size="2", weight="medium"),
                        rx.select(
                            ["B2B", "B2C", "Both"],
                            name="business_type",
                            default_value=btype_val,
                            size="2",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Directory URL *", size="2", weight="medium"),
                        rx.input(name="url", default_value=url_val,
                                 placeholder="https://www.yellowpages.com/...", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray",
                                                  size="2", on_click=close_fn)),
                        rx.button("Save", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end", spacing="3", width="100%",
                    ),
                    spacing="4", width="100%",
                ),
                on_submit=on_submit,
                width="100%",
            ),
            max_width="480px", width="100%", padding="24px",
        ),
        open=open_var,
        on_open_change=on_open,
    )


def cs_row(s) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(s["country"], size="2", weight="medium"), style=TD_STYLE),
        rx.table.cell(
            rx.badge(
                s["business_type"],
                color_scheme=rx.cond(s["business_type"] == "B2B", "blue",
                                     rx.cond(s["business_type"] == "B2C", "green", "gray")),
                variant="soft", size="1",
            ),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.text(s["url"], size="1", color="#6b7280",
                    style={"word_break": "break-all", "max_width": "400px"}),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.switch(
                checked=s["is_active"].bool(),
                on_change=MastersState.toggle_cs(s["id"], s["is_active"]),
                size="1",
            ),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=MastersState.open_edit_cs_modal(s["id"]),
                    variant="ghost", size="1", color_scheme="violet", title="Edit",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=MastersState.delete_cs(s["id"]),
                    variant="ghost", size="1", color_scheme="red", title="Delete",
                ),
                spacing="1",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


def country_sources_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Country Sources", size="3", weight="bold"),
            rx.spacer(),
            rx.input(
                placeholder="Filter by country…",
                value=MastersState.cs_filter_country,
                on_change=MastersState.set_cs_filter_country,
                size="2",
                width="200px",
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Add Source",
                on_click=MastersState.open_add_cs_modal,
                size="2",
                style={"background_color": PRIMARY, "color": "white"},
            ),
            align="center",
            width="100%",
            spacing="3",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Country", "Type", "URL", "Active", "Actions"]],
                    )
                ),
                rx.table.body(rx.foreach(MastersState.filtered_country_sources, cs_row)),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
            overflow_x="auto",
        ),
        _cs_modal(
            "Add Country Source", "", "Both", "",
            MastersState.add_cs,
            MastersState.show_add_cs_modal,
            MastersState.set_show_add_cs_modal,
            MastersState.close_add_cs_modal,
        ),
        _cs_modal(
            "Edit Country Source",
            MastersState.cs_country,
            MastersState.cs_business_type,
            MastersState.cs_url,
            MastersState.save_edit_cs,
            MastersState.show_edit_cs_modal,
            MastersState.set_show_edit_cs_modal,
            MastersState.close_edit_cs_modal,
        ),
        spacing="4", width="100%",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Masters Page
# ─────────────────────────────────────────────────────────────────────────────

def masters_content() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger(
                rx.hstack(rx.icon("building_2", size=14), rx.text("Company Profile"), spacing="2"),
                value="company",
            ),
            rx.tabs.trigger(
                rx.hstack(rx.icon("package", size=14), rx.text("Products"), spacing="2"),
                value="products",
            ),
            rx.tabs.trigger(
                rx.hstack(rx.icon("target", size=14), rx.text("Target Audience"), spacing="2"),
                value="audience",
            ),
            rx.tabs.trigger(
                rx.hstack(rx.icon("mail", size=14), rx.text("Email Templates"), spacing="2"),
                value="templates",
            ),
            rx.tabs.trigger(
                rx.hstack(rx.icon("globe", size=14), rx.text("Country Sources"), spacing="2"),
                value="sources",
            ),
        ),
        rx.tabs.content(company_profile_tab(),   value="company",   padding_top="24px"),
        rx.tabs.content(products_tab(),          value="products",  padding_top="24px"),
        rx.tabs.content(target_audience_tab(),   value="audience",  padding_top="24px"),
        rx.tabs.content(templates_tab(),         value="templates", padding_top="24px"),
        rx.tabs.content(country_sources_tab(),   value="sources",   padding_top="24px"),
        value=MastersState.active_tab,
        on_change=MastersState.set_tab,
        width="100%",
    )


@rx.page(
    route="/masters",
    on_load=[AuthState.check_auth, AppState.load_products, MastersState.load_masters],
)
def masters():
    return layout(
        masters_content(),
        title="Masters",
        subtitle="Manage company profile, products, target audience & templates",
    )
