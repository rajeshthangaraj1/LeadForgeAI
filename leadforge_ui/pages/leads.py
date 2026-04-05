import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.components.tables import stage_badge, empty_state
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.leads_state import LeadsState
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER, CARD_STYLE, TD_STYLE


STAGE_OPTIONS = ["New", "Contacted", "Replied", "Qualified", "Won", "Lost"]


# ── Filter bar ────────────────────────────────────────────────────────────────

def filter_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.input(
                placeholder="Search name, company, email…",
                value=LeadsState.search_query,
                on_change=LeadsState.set_search_query,
                size="2",
                width="260px",
            ),
            rx.select(
                LeadsState.industry_options,
                value=LeadsState.filter_industry,
                on_change=LeadsState.set_filter_industry,
                placeholder="Industry",
                size="2",
            ),
            rx.select(
                LeadsState.location_options,
                value=LeadsState.filter_location,
                on_change=LeadsState.set_filter_location,
                placeholder="Location",
                size="2",
            ),
            rx.select(
                ["New", "Contacted", "Replied", "Qualified", "Won", "Lost"],
                value=LeadsState.filter_stage,
                on_change=LeadsState.set_filter_stage,
                placeholder="Stage",
                size="2",
            ),
            rx.button(
                rx.icon("x", size=14),
                "Clear",
                on_click=LeadsState.clear_filters,
                variant="soft",
                size="2",
            ),
            rx.spacer(),
            rx.text(LeadsState.leads_count_label, size="2", color="#6b7280"),
            align="center",
            spacing="3",
            flex_wrap="wrap",
        ),
        background_color="white",
        padding="16px",
        border_radius="12px",
        border=f"1px solid {BORDER}",
    )


# ── Lead table row ────────────────────────────────────────────────────────────

def _dash(val: rx.Var) -> rx.Component:
    """Show val if truthy, else '—'. Use instead of `val or '—'`."""
    return rx.cond(val, val, "—")


def lead_row(lead) -> rx.Component:
    return rx.table.row(
        # ── Checkbox ───────────────────────────────────────────────────────────
        rx.table.cell(
            rx.checkbox(
                checked=lead["selected"],
                on_change=LeadsState.toggle_lead_selection(lead["id"]),
            ),
            style={**TD_STYLE, "width": "40px"},
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(_dash(lead["name"]), size="2", weight="medium"),
                rx.text(rx.cond(lead["role"], lead["role"], ""), size="1", color="#6b7280"),
                spacing="0",
                align_items="start",
            ),
            style=TD_STYLE,
        ),
        rx.table.cell(rx.text(_dash(lead["company"]), size="2"), style=TD_STYLE),
        rx.table.cell(
            rx.cond(
                lead["email"],
                rx.link(lead["email"], href="mailto:" + lead["email"], size="2"),
                rx.text("—", size="2"),
            ),
            style=TD_STYLE,
        ),
        rx.table.cell(rx.text(_dash(lead["phone"]), size="2"), style=TD_STYLE),
        rx.table.cell(rx.text(_dash(lead["industry"]), size="2"), style=TD_STYLE),
        rx.table.cell(rx.text(_dash(lead["location"]), size="2"), style=TD_STYLE),
        rx.table.cell(
            stage_badge(rx.cond(lead["stage"], lead["stage"], "new")),
            style=TD_STYLE,
        ),
        rx.table.cell(
            rx.text(lead["score"], size="2"),
            style=TD_STYLE,
        ),
        # ── Actions ────────────────────────────────────────────────────────────
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=LeadsState.open_edit_modal(lead["id"]),
                    variant="ghost",
                    size="1",
                    color_scheme="violet",
                    title="Edit",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=LeadsState.open_delete_confirm(lead["id"], lead["name"]),
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    title="Delete",
                ),
                spacing="1",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


# ── Edit Lead Modal ───────────────────────────────────────────────────────────

def edit_lead_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Edit Lead"),
            rx.form(
                rx.vstack(
                    rx.grid(
                        rx.vstack(
                            rx.text("Name", size="2", weight="medium"),
                            rx.input(name="name", default_value=LeadsState.edit_name, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Company", size="2", weight="medium"),
                            rx.input(name="company", default_value=LeadsState.edit_company, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Role / Title", size="2", weight="medium"),
                            rx.input(name="role", default_value=LeadsState.edit_role, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Email", size="2", weight="medium"),
                            rx.input(name="email", default_value=LeadsState.edit_email, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Phone", size="2", weight="medium"),
                            rx.input(name="phone", default_value=LeadsState.edit_phone, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("LinkedIn", size="2", weight="medium"),
                            rx.input(name="linkedin", default_value=LeadsState.edit_linkedin, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Industry", size="2", weight="medium"),
                            rx.input(name="industry", default_value=LeadsState.edit_industry, size="2"),
                            spacing="1", align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Location", size="2", weight="medium"),
                            rx.input(name="location", default_value=LeadsState.edit_location, size="2"),
                            spacing="1", align_items="start",
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Stage", size="2", weight="medium"),
                        rx.select(
                            STAGE_OPTIONS,
                            name="stage",
                            default_value=LeadsState.edit_stage,
                            size="2",
                        ),
                        spacing="1", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("Notes", size="2", weight="medium"),
                        rx.text_area(
                            name="notes",
                            default_value=LeadsState.edit_notes,
                            placeholder="Add notes…",
                            rows="3",
                            size="2",
                            width="100%",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=LeadsState.close_edit_modal),
                        ),
                        rx.button("Save Changes", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end",
                        spacing="3",
                        width="100%",
                    ),
                    spacing="5",
                    width="100%",
                ),
                on_submit=LeadsState.save_edit_lead,
                width="100%",
            ),
            max_width="640px",
            padding="32px",
        ),
        open=LeadsState.show_edit_modal,
        on_open_change=LeadsState.set_show_edit_modal,
    )


# ── Delete confirm dialog ─────────────────────────────────────────────────────

def delete_confirm_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Lead"),
            rx.alert_dialog.description(
                rx.text("Are you sure you want to delete "),
                rx.text(LeadsState.delete_lead_name, weight="bold"),
                rx.text("? This action cannot be undone."),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Cancel", variant="soft", color_scheme="gray",
                              on_click=LeadsState.cancel_delete),
                ),
                rx.alert_dialog.action(
                    rx.button("Delete", color_scheme="red", on_click=LeadsState.confirm_delete),
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
            ),
        ),
        open=LeadsState.show_delete_confirm,
        on_open_change=LeadsState.set_show_delete_confirm,
    )


# ── Pagination ────────────────────────────────────────────────────────────────

def pagination() -> rx.Component:
    return rx.hstack(
        rx.text(
            f"Page ",
            rx.text.span(LeadsState.page, weight="bold"),
            " of ",
            rx.text.span(LeadsState.total_pages, weight="bold"),
            size="2",
            color="#6b7280",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("chevron_left", size=14),
            "Prev",
            on_click=LeadsState.prev_page,
            variant="soft",
            size="2",
            disabled=LeadsState.page <= 1,
        ),
        rx.button(
            "Next",
            rx.icon("chevron_right", size=14),
            on_click=LeadsState.next_page,
            variant="soft",
            size="2",
            disabled=LeadsState.page >= LeadsState.total_pages,
        ),
        align="center",
        spacing="3",
        padding_top="12px",
    )


# ── Bulk action bar ───────────────────────────────────────────────────────────

def bulk_action_bar() -> rx.Component:
    return rx.cond(
        LeadsState.has_selection,
        rx.hstack(
            rx.text(
                LeadsState.selection_count,
                " lead(s) selected",
                size="2",
                weight="medium",
                color="#92400e",
            ),
            rx.cond(
                ~LeadsState.all_filtered_selected,
                rx.button(
                    "Select all ",
                    rx.text.span(LeadsState.leads_count_label, weight="bold"),
                    " in view",
                    on_click=LeadsState.select_all_filtered,
                    variant="ghost",
                    size="2",
                    color_scheme="orange",
                ),
                rx.box(),
            ),
            rx.spacer(),
            rx.button(
                rx.icon("trash_2", size=14),
                "Delete Selected",
                on_click=LeadsState.open_bulk_delete_confirm,
                variant="soft",
                size="2",
                color_scheme="red",
            ),
            rx.button(
                rx.icon("x", size=14),
                "Clear",
                on_click=LeadsState.clear_selection,
                variant="ghost",
                size="2",
                color_scheme="gray",
            ),
            align="center",
            spacing="3",
            padding="10px 16px",
            background_color="#fef3c7",
            border_radius="8px",
            border="1px solid #fde68a",
            width="100%",
        ),
        rx.box(),
    )


def bulk_delete_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Selected Leads"),
            rx.alert_dialog.description(
                rx.text("Delete "),
                rx.text(LeadsState.selection_count, weight="bold"),
                rx.text(" lead(s)? This cannot be undone."),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Cancel", variant="soft", color_scheme="gray",
                              on_click=LeadsState.cancel_bulk_delete),
                ),
                rx.alert_dialog.action(
                    rx.button("Delete", color_scheme="red",
                              on_click=LeadsState.confirm_bulk_delete),
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
            ),
        ),
        open=LeadsState.show_bulk_delete_confirm,
        on_open_change=LeadsState.set_show_bulk_delete_confirm,
    )


# ── Import / Export bar ───────────────────────────────────────────────────────

def import_export_bar() -> rx.Component:
    return rx.hstack(
        rx.upload(
            rx.button(
                rx.icon("upload", size=14),
                "Import CSV",
                variant="soft",
                size="2",
                color_scheme="gray",
            ),
            id="leads_csv_upload",
            accept={".csv": "text/csv"},
            max_files=1,
            # collapse upload wrapper to button height — no dashed border
            border="none",
            padding="0",
            display="inline-flex",
        ),
        rx.button(
            rx.icon("check", size=14),
            "Process Import",
            on_click=LeadsState.handle_csv_import(rx.upload_files(upload_id="leads_csv_upload")),
            variant="soft",
            size="2",
            color_scheme="violet",
        ),
        rx.button(
            rx.icon("file-down", size=14),
            "Sample CSV",
            on_click=LeadsState.download_sample_csv,
            variant="soft",
            size="2",
            color_scheme="amber",
        ),
        rx.button(
            rx.icon("download", size=14),
            "Export CSV",
            on_click=LeadsState.export_leads_csv,
            variant="soft",
            size="2",
            color_scheme="grass",
        ),
        rx.cond(
            LeadsState.import_status != "",
            rx.text(LeadsState.import_status, size="1", color="#6b7280"),
            rx.box(),
        ),
        align="center",
        spacing="2",
    )


def leads_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(flex="1"),
            import_export_bar(),
            align="center",
            width="100%",
        ),
        filter_bar(),
        bulk_action_bar(),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(
                            rx.checkbox(
                                checked=LeadsState.all_page_selected,
                                on_change=LeadsState.toggle_all_page,
                            ),
                            width="40px",
                        ),
                        *[rx.table.column_header_cell(h) for h in
                          ["Name / Role", "Company", "Email", "Phone",
                           "Industry", "Location", "Stage", "Score", "Actions"]],
                    )
                ),
                rx.table.body(
                    rx.foreach(LeadsState.paged_leads_with_sel, lead_row)
                ),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
            overflow_x="auto",
        ),
        pagination(),
        edit_lead_modal(),
        delete_confirm_dialog(),
        bulk_delete_dialog(),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/leads",
    on_load=[AuthState.check_auth, LeadsState.load_leads],
)
def leads():
    return layout(
        leads_content(),
        title="Leads Management",
        subtitle="View, filter and manage your leads pipeline",
    )
