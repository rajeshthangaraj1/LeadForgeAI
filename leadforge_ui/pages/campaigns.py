import reflex as rx
from leadforge_ui.components.layout import layout
from leadforge_ui.state.auth import AuthState
from leadforge_ui.state.campaigns_state import CampaignsState
from leadforge_ui.styles.theme import PRIMARY, PRIMARY_DARK, BORDER, TD_STYLE


# ── Campaign status badge ─────────────────────────────────────────────────────

def campaign_badge(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        ("draft",  rx.badge("Draft",  color_scheme="gray",   variant="soft")),
        ("sent",   rx.badge("Sent",   color_scheme="green",  variant="soft")),
        ("active", rx.badge("Active", color_scheme="blue",   variant="soft")),
        rx.badge(status, color_scheme="gray", variant="soft"),
    )


# ── Campaign table row ────────────────────────────────────────────────────────

def campaign_row(c) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c["name"], size="2", weight="medium"), style=TD_STYLE),
        rx.table.cell(rx.text(rx.cond(c["template_name"], c["template_name"], "—"), size="2"), style=TD_STYLE),
        rx.table.cell(campaign_badge(c["status"]), style=TD_STYLE),
        rx.table.cell(rx.text(c["sent_count"], size="2"), style=TD_STYLE),
        rx.table.cell(rx.text(rx.cond(c["created_at"], c["created_at"][:16], "—"), size="2"), style=TD_STYLE),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("bar_chart_2", size=14),
                    "Stats",
                    on_click=CampaignsState.open_stats_modal(c["id"]),
                    variant="soft",
                    size="1",
                    color_scheme="violet",
                ),
                rx.cond(
                    c["status"] == "draft",
                    rx.button(
                        rx.icon("send", size=14),
                        "Send",
                        on_click=CampaignsState.send_campaign(c["id"]),
                        variant="soft",
                        size="1",
                        color_scheme="green",
                        loading=CampaignsState.sending,
                    ),
                    rx.box(),
                ),
                rx.button(
                    rx.icon("refresh_cw", size=14),
                    "Check Replies",
                    on_click=CampaignsState.check_replies(c["id"]),
                    variant="soft",
                    size="1",
                    color_scheme="blue",
                    loading=CampaignsState.checking_replies,
                    title="Scan inbox for replies to this campaign",
                ),
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=CampaignsState.open_edit_modal(c["id"]),
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    title="Rename campaign",
                ),
                rx.icon_button(
                    rx.icon("trash_2", size=14),
                    on_click=CampaignsState.open_delete_confirm(c["id"]),
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    title="Delete campaign",
                ),
                spacing="2",
            ),
            style=TD_STYLE,
        ),
        _hover={"background_color": "#fafafa"},
    )


# ── Create Campaign Modal ─────────────────────────────────────────────────────

def create_campaign_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("plus", size=16),
                "New Campaign",
                on_click=CampaignsState.open_create_modal,
                style={"background_color": PRIMARY, "color": "white"},
                size="2",
            ),
        ),
        rx.dialog.content(
            rx.dialog.title("Create Campaign"),
            rx.dialog.description("Configure and create a new email campaign."),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Campaign Name *", size="2", weight="medium"),
                        rx.input(name="name", placeholder="e.g. Q1 Outreach UAE", size="2", width="100%"),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Email Template *", size="2", weight="medium"),
                        rx.select(
                            CampaignsState.template_names,
                            name="template_id",
                            placeholder="Select template",
                            size="2",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Product (optional)", size="2", weight="medium"),
                        rx.select(
                            CampaignsState.product_names_list,
                            name="product_id",
                            placeholder="All products",
                            size="2",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=CampaignsState.close_create_modal),
                        ),
                        rx.button("Create Campaign", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end",
                        spacing="3",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                on_submit=CampaignsState.create_campaign,
                width="100%",
            ),
            max_width="480px",
            padding="32px",
        ),
        open=CampaignsState.show_create_modal,
        on_open_change=CampaignsState.set_show_create_modal,
    )


# ── Edit Campaign Modal ───────────────────────────────────────────────────────

def edit_campaign_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rename Campaign"),
            rx.form(
                rx.vstack(
                    rx.vstack(
                        rx.text("Campaign Name", size="2", weight="medium"),
                        rx.input(
                            name="name",
                            default_value=CampaignsState.edit_campaign_name,
                            size="2",
                            width="100%",
                        ),
                        spacing="1", align_items="start", width="100%",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancel", variant="soft", color_scheme="gray", size="2",
                                      on_click=CampaignsState.close_edit_modal),
                        ),
                        rx.button("Save", type="submit", size="2",
                                  style={"background_color": PRIMARY, "color": "white"}),
                        justify="end",
                        spacing="3",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                on_submit=CampaignsState.save_edit_campaign,
                width="100%",
            ),
            max_width="400px",
            padding="28px",
        ),
        open=CampaignsState.show_edit_modal,
        on_open_change=CampaignsState.set_show_edit_modal,
    )


# ── Delete Confirm Dialog ─────────────────────────────────────────────────────

def delete_campaign_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Campaign"),
            rx.alert_dialog.description(
                rx.text("Delete campaign "),
                rx.text(CampaignsState.delete_campaign_name, weight="bold"),
                rx.text("? All send records for this campaign will also be deleted."),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button("Cancel", variant="soft", color_scheme="gray",
                              on_click=CampaignsState.cancel_delete),
                ),
                rx.alert_dialog.action(
                    rx.button("Delete", color_scheme="red", on_click=CampaignsState.confirm_delete),
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
            ),
        ),
        open=CampaignsState.show_delete_confirm,
        on_open_change=CampaignsState.set_show_delete_confirm,
    )


# ── Stats Modal ───────────────────────────────────────────────────────────────

def stats_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(CampaignsState.selected_campaign["name"]),
            rx.vstack(
                rx.cond(
                    CampaignsState.reply_check_result != "",
                    rx.callout(
                        CampaignsState.reply_check_result,
                        icon="info",
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                    ),
                    rx.box(),
                ),
                rx.grid(
                    rx.box(
                        rx.text("Total", size="1", color="#6b7280"),
                        rx.heading(CampaignsState.campaign_stats["total"], size="6"),
                        padding="16px", border_radius="8px",
                        background_color="#f9fafb", border=f"1px solid {BORDER}",
                    ),
                    rx.box(
                        rx.text("Sent", size="1", color="#6b7280"),
                        rx.heading(CampaignsState.campaign_stats["sent"], size="6"),
                        padding="16px", border_radius="8px",
                        background_color="#eff6ff", border=f"1px solid #bfdbfe",
                    ),
                    rx.box(
                        rx.text("Replied", size="1", color="#6b7280"),
                        rx.heading(CampaignsState.campaign_stats["replied"], size="6"),
                        padding="16px", border_radius="8px",
                        background_color="#f0fdf4", border=f"1px solid #bbf7d0",
                    ),
                    rx.box(
                        rx.text("Auto-Reply", size="1", color="#6b7280"),
                        rx.heading(CampaignsState.campaign_stats["auto_reply"], size="6"),
                        padding="16px", border_radius="8px",
                        background_color="#fafafa", border=f"1px solid {BORDER}",
                    ),
                    rx.box(
                        rx.text("Reply Rate", size="1", color="#6b7280"),
                        rx.heading(CampaignsState.campaign_stats["reply_rate"], size="6"),
                        padding="16px", border_radius="8px",
                        background_color="#faf5ff", border=f"1px solid #e9d5ff",
                    ),
                    columns="3",
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("refresh_cw", size=14),
                        "Check Replies",
                        on_click=CampaignsState.check_replies(CampaignsState.selected_campaign["id"]),
                        variant="soft",
                        color_scheme="blue",
                        size="2",
                        loading=CampaignsState.checking_replies,
                    ),
                    rx.dialog.close(
                        rx.button("Close", variant="soft", color_scheme="gray", size="2",
                                  on_click=CampaignsState.close_stats_modal),
                    ),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            max_width="640px",
            padding="32px",
        ),
        open=CampaignsState.show_stats_modal,
        on_open_change=CampaignsState.set_show_stats_modal,
    )


# ── Send progress ─────────────────────────────────────────────────────────────

def send_progress_bar() -> rx.Component:
    return rx.cond(
        CampaignsState.sending,
        rx.callout(
            rx.hstack(
                rx.spinner(size="2"),
                rx.text(
                    f"Sending… {CampaignsState.send_progress} / {CampaignsState.send_total}",
                    size="2",
                ),
                spacing="3",
                align="center",
            ),
            color_scheme="blue",
            variant="soft",
        ),
        rx.box(),
    )


# ── Campaigns content ─────────────────────────────────────────────────────────

def campaigns_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Email Campaigns", size="4"),
            rx.spacer(),
            create_campaign_modal(),
            align="center",
            width="100%",
        ),
        send_progress_bar(),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[rx.table.column_header_cell(h) for h in
                          ["Name", "Template", "Status", "Emails Sent", "Created", "Actions"]],
                    )
                ),
                rx.table.body(
                    rx.foreach(CampaignsState.campaigns, campaign_row),
                ),
                width="100%",
            ),
            background_color="white",
            border_radius="12px",
            border=f"1px solid {BORDER}",
            overflow_x="auto",
        ),
        stats_modal(),
        edit_campaign_modal(),
        delete_campaign_dialog(),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/campaigns",
    on_load=[AuthState.check_auth, CampaignsState.load_campaigns],
)
def campaigns():
    return layout(
        campaigns_content(),
        title="Email Campaigns",
        subtitle="Create, send and track email campaigns",
    )
