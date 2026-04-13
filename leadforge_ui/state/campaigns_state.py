import reflex as rx
import sys, os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leadforge_ui.state.auth import AuthState
from database.sqlite_db import (
    get_email_campaigns,
    get_email_templates,
    get_products,
    get_company_profile,
    create_email_campaign,
    get_campaign_analytics,
    get_sends_for_campaign,
    get_leads_for_campaign,
    get_gmail_config,
    log_email_send,
    update_campaign_status,
    mark_lead_emailed,
    get_email_template_by_id,
    delete_email_campaign,
    update_email_campaign_name,
    update_lead_stage,
    update_send_replied,
    update_send_replied_by_email,
)
from utils.email_utils import send_email, render_template, fetch_replies


class CampaignDict(TypedDict):
    id: int
    name: str
    status: str
    sent_count: int
    template_id: int
    product_id: int
    created_at: str
    template_name: str


class SelectedCampaign(TypedDict):
    id: int
    name: str
    status: str
    template_id: int
    product_id: int
    sent_count: int
    created_at: str


class CampaignStats(TypedDict):
    total: int
    sent: int
    replied: int
    auto_reply: int
    failed: int
    reply_rate: float


class TemplateRef(TypedDict):
    id: int
    name: str
    subject: str
    body: str
    created_at: str


class ProductRef(TypedDict):
    id: int
    product_name: str
    description: str
    created_at: str


def _normalize_campaign(c: dict) -> CampaignDict:
    return {
        "id": int(c.get("id") or 0),
        "name": str(c.get("name") or ""),
        "status": str(c.get("status") or "draft"),
        "sent_count": int(c.get("sent_count") or 0),
        "template_id": int(c.get("template_id") or 0),
        "product_id": int(c.get("product_id") or 0),
        "created_at": str(c.get("created_at") or ""),
        "template_name": str(c.get("template_name") or ""),
    }


class CampaignsState(AuthState):
    """CRUD + send logic for Email Campaigns."""

    campaigns: list[CampaignDict] = []
    templates: list[TemplateRef] = []
    products: list[ProductRef] = []

    # ── Create modal ───────────────────────────────────────────────────────────
    show_create_modal: bool = False
    new_campaign_name: str = ""
    new_template_id: str = ""
    new_product_id: str = ""

    # ── Edit modal ─────────────────────────────────────────────────────────────
    show_edit_modal: bool = False
    edit_campaign_id: int = 0
    edit_campaign_name: str = ""

    # ── Delete confirm ─────────────────────────────────────────────────────────
    show_delete_confirm: bool = False
    delete_campaign_id: int = 0
    delete_campaign_name: str = ""

    # ── Campaign detail / stats ────────────────────────────────────────────────
    show_stats_modal: bool = False
    selected_campaign: SelectedCampaign = {
        "id": 0, "name": "", "status": "draft",
        "template_id": 0, "product_id": 0, "sent_count": 0, "created_at": "",
    }
    campaign_stats: CampaignStats = {
        "total": 0, "sent": 0, "replied": 0,
        "auto_reply": 0, "failed": 0, "reply_rate": 0.0,
    }
    campaign_sends: list[dict] = []

    # ── Send progress ──────────────────────────────────────────────────────────
    sending: bool = False
    send_progress: int = 0
    send_total: int = 0

    # ── Reply check ────────────────────────────────────────────────────────────
    checking_replies: bool = False
    reply_check_result: str = ""

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_campaigns(self):
        raw = get_email_campaigns(self.user_id)
        self.campaigns = [_normalize_campaign(c) for c in raw]
        raw_templates = get_email_templates(self.user_id)
        self.templates = [
            {
                "id": int(t.get("id") or 0),
                "name": str(t.get("name") or ""),
                "subject": str(t.get("subject") or ""),
                "body": str(t.get("body") or ""),
                "created_at": str(t.get("created_at") or ""),
            }
            for t in raw_templates
        ]
        profile = get_company_profile(self.user_id)
        if profile:
            raw_prods = get_products(profile["id"])
            self.products = [
                {
                    "id": int(p.get("id") or 0),
                    "product_name": str(p.get("product_name") or ""),
                    "description": str(p.get("description") or ""),
                    "created_at": str(p.get("created_at") or ""),
                }
                for p in raw_prods
            ]

    # ── Create modal ───────────────────────────────────────────────────────────

    def open_create_modal(self):
        self.new_campaign_name = ""
        self.new_template_id = str(self.templates[0]["id"]) if self.templates else ""
        self.new_product_id = str(self.products[0]["id"]) if self.products else ""
        self.show_create_modal = True

    def close_create_modal(self):
        self.show_create_modal = False

    def set_show_create_modal(self, val: bool):
        self.show_create_modal = val

    def create_campaign(self, form_data: dict):
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Campaign name is required.")
        tpl_name = form_data.get("template_id", "")
        tpl = next((t for t in self.templates if t["name"] == tpl_name), None)
        if not tpl:
            tpl = self.templates[0] if self.templates else None
        if not tpl:
            return rx.toast.error("Select a template first.")
        template_id = tpl["id"]
        prod_name = form_data.get("product_id", "")
        prod = next((p for p in self.products if p["product_name"] == prod_name), None)
        product_id = prod["id"] if prod else None

        create_email_campaign(name, template_id, product_id, user_id=self.user_id)
        self.show_create_modal = False
        self.load_campaigns()
        return rx.toast.success("Campaign created.")

    # ── Edit modal ─────────────────────────────────────────────────────────────

    def open_edit_modal(self, campaign_id: int):
        camp = next((c for c in self.campaigns if c["id"] == campaign_id), None)
        if not camp:
            return
        self.edit_campaign_id = campaign_id
        self.edit_campaign_name = camp["name"]
        self.show_edit_modal = True

    def close_edit_modal(self):
        self.show_edit_modal = False

    def set_show_edit_modal(self, val: bool):
        self.show_edit_modal = val

    def save_edit_campaign(self, form_data: dict):
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Campaign name cannot be empty.")
        update_email_campaign_name(self.edit_campaign_id, name)
        self.show_edit_modal = False
        self.load_campaigns()
        return rx.toast.success("Campaign renamed.")

    # ── Delete ─────────────────────────────────────────────────────────────────

    def open_delete_confirm(self, campaign_id: int):
        camp = next((c for c in self.campaigns if c["id"] == campaign_id), None)
        if not camp:
            return
        self.delete_campaign_id = campaign_id
        self.delete_campaign_name = camp["name"]
        self.show_delete_confirm = True

    def cancel_delete(self):
        self.show_delete_confirm = False

    def set_show_delete_confirm(self, val: bool):
        self.show_delete_confirm = val

    def confirm_delete(self):
        delete_email_campaign(self.delete_campaign_id)
        self.show_delete_confirm = False
        self.load_campaigns()
        return rx.toast.success("Campaign deleted.")

    # ── Stats modal ────────────────────────────────────────────────────────────

    def open_stats_modal(self, campaign_id: int):
        camp = next((c for c in self.campaigns if c["id"] == campaign_id), None)
        if not camp:
            return
        self.selected_campaign = {
            "id": camp["id"],
            "name": camp["name"],
            "status": camp["status"],
            "template_id": camp["template_id"],
            "product_id": camp["product_id"],
            "sent_count": camp["sent_count"],
            "created_at": camp["created_at"],
        }
        raw_stats = get_campaign_analytics(campaign_id)
        self.campaign_stats = {
            "total": int(raw_stats.get("total") or 0),
            "sent": int(raw_stats.get("sent") or 0),
            "replied": int(raw_stats.get("replied") or 0),
            "auto_reply": int(raw_stats.get("auto_reply") or 0),
            "failed": int(raw_stats.get("failed") or 0),
            "reply_rate": float(raw_stats.get("reply_rate") or 0.0),
        }
        self.campaign_sends = get_sends_for_campaign(campaign_id)[:50]
        self.show_stats_modal = True

    def close_stats_modal(self):
        self.show_stats_modal = False

    def set_show_stats_modal(self, val: bool):
        self.show_stats_modal = val

    # ── Send campaign ──────────────────────────────────────────────────────────

    @rx.event(background=True)
    async def send_campaign(self, campaign_id: int):
        async with self:
            self.sending = True
            self.send_progress = 0
            _uid = self.user_id
            camp = next((c for c in self.campaigns if c["id"] == campaign_id), None)

        gmail = get_gmail_config(_uid)
        if not gmail:
            async with self:
                self.sending = False
            return rx.toast.error("Configure Gmail in Settings first.")

        if not camp:
            async with self:
                self.sending = False
            return

        template = get_email_template_by_id(camp["template_id"])
        if not template:
            async with self:
                self.sending = False
            return rx.toast.error("Template not found.")

        leads = get_leads_for_campaign(
            product_id=camp["product_id"] or None,
            user_id=_uid,
            only_with_email=True,
        )

        async with self:
            self.send_total = len(leads)

        sent = 0
        for i, lead in enumerate(leads):
            subj, body = render_template(template["subject"], template["body"], lead)
            ok, msg_id, err = send_email(
                gmail["email"],
                gmail["app_password"],
                lead["email"],
                subj,
                body,
                gmail.get("smtp_host", "smtp.gmail.com"),
                gmail.get("smtp_port", 587),
            )
            status = "sent" if ok else "failed"
            log_email_send(campaign_id, lead["id"], lead["email"], subj, status, msg_id or "")
            if ok:
                mark_lead_emailed(lead["id"])
                update_lead_stage(lead["id"], "contacted")
                sent += 1
            async with self:
                self.send_progress = i + 1

        update_campaign_status(campaign_id, "sent", sent)
        async with self:
            self.sending = False
            self.load_campaigns()
        return rx.toast.success(f"Campaign sent — {sent} emails delivered.")

    # ── Check replies ──────────────────────────────────────────────────────────

    @rx.event(background=True)
    async def check_replies(self, campaign_id: int):
        async with self:
            self.checking_replies = True
            self.reply_check_result = ""
            _uid = self.user_id

        try:
            gmail = get_gmail_config(_uid)
            if not gmail:
                async with self:
                    self.checking_replies = False
                    self.reply_check_result = "Gmail not configured."
                return rx.toast.error("Configure Gmail in Settings first.")

            sends = get_sends_for_campaign(campaign_id)
            msg_ids = [s["message_id"] for s in sends if s.get("message_id")]
            to_emails = [s["email_to"] for s in sends if s.get("email_to")]

            replies = fetch_replies(
                gmail["email"],
                gmail["app_password"],
                sent_message_ids=msg_ids,
                sent_to_emails=to_emails,
                imap_host=gmail.get("imap_host", "imap.gmail.com"),
                imap_port=int(gmail.get("imap_port", 993)),
            )

            real = 0
            auto = 0
            for reply in replies:
                is_auto = reply.get("is_auto_reply", False)
                if reply.get("matched_by") == "message_id":
                    update_send_replied(reply["in_reply_to"], is_auto=is_auto)
                else:
                    update_send_replied_by_email(reply["sender_email"], is_auto=is_auto)

                # Update lead stage if real reply
                if not is_auto:
                    real += 1
                    # Find lead id from sends
                    matched_send = next(
                        (s for s in sends if s.get("email_to", "").lower() == reply["sender_email"].lower()),
                        None,
                    )
                    if matched_send and matched_send.get("lead_id"):
                        update_lead_stage(matched_send["lead_id"], "replied")
                else:
                    auto += 1

            result_msg = f"Found {len(replies)} replies: {real} real, {auto} auto-replies."
            async with self:
                self.checking_replies = False
                self.reply_check_result = result_msg
                # Refresh stats if stats modal is open
                if self.show_stats_modal and self.selected_campaign["id"] == campaign_id:
                    raw_stats = get_campaign_analytics(campaign_id)
                    self.campaign_stats = {
                        "total": int(raw_stats.get("total") or 0),
                        "sent": int(raw_stats.get("sent") or 0),
                        "replied": int(raw_stats.get("replied") or 0),
                        "auto_reply": int(raw_stats.get("auto_reply") or 0),
                        "failed": int(raw_stats.get("failed") or 0),
                        "reply_rate": float(raw_stats.get("reply_rate") or 0.0),
                    }
            async with self:
                self.load_campaigns()
            return rx.toast.success(result_msg)

        except Exception as e:
            async with self:
                self.checking_replies = False
                self.reply_check_result = f"Error: {e}"
            return rx.toast.error(f"Reply check failed: {e}")

    # ── Computed ────────────────────────────────────────────────────────────────

    @rx.var
    def template_names(self) -> list[str]:
        return [t["name"] for t in self.templates if t["name"]]

    @rx.var
    def product_names_list(self) -> list[str]:
        return [p["product_name"] for p in self.products if p["product_name"]]
