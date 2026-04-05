import reflex as rx
import sys, os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.sqlite_db import (
    get_company_profile,
    save_company_profile,
    get_products,
    save_product,
    delete_product,
    get_all_target_audiences,
    add_target_audience,
    update_target_audience,
    delete_target_audience,
    get_email_templates,
    save_email_template,
    delete_email_template,
    get_email_template_by_id,
    get_all_country_sources,
    add_country_source,
    update_country_source,
    delete_country_source,
    toggle_country_source,
)


class ProductDict(TypedDict):
    id: int
    product_name: str
    description: str
    created_at: str


class TemplateDict(TypedDict):
    id: int
    name: str
    subject: str
    body: str
    created_at: str


def _normalize_product(p: dict) -> ProductDict:
    return {
        "id": int(p.get("id") or 0),
        "product_name": str(p.get("product_name") or ""),
        "description": str(p.get("description") or ""),
        "created_at": str(p.get("created_at") or ""),
    }


class TargetAudienceDict(TypedDict):
    id: int
    product_id: int
    industry: str
    location: str
    country: str
    business_type: str
    roles: str
    company_size: str
    keywords: str
    competitors: str
    created_at: str


def _normalize_ta(t: dict) -> TargetAudienceDict:
    return {
        "id": int(t.get("id") or 0),
        "product_id": int(t.get("product_id") or 0),
        "industry": str(t.get("industry") or ""),
        "location": str(t.get("location") or ""),
        "country": str(t.get("country") or ""),
        "business_type": str(t.get("business_type") or "B2B"),
        "roles": str(t.get("roles") or ""),
        "company_size": str(t.get("company_size") or ""),
        "keywords": str(t.get("keywords") or ""),
        "competitors": str(t.get("competitors") or ""),
        "created_at": str(t.get("created_at") or ""),
    }


class CountrySourceDict(TypedDict):
    id: int
    country: str
    business_type: str
    url: str
    is_active: int
    created_at: str


def _normalize_country_source(s: dict) -> CountrySourceDict:
    return {
        "id": int(s.get("id") or 0),
        "country": str(s.get("country") or ""),
        "business_type": str(s.get("business_type") or "Both"),
        "url": str(s.get("url") or ""),
        "is_active": int(s.get("is_active") if s.get("is_active") is not None else 1),
        "created_at": str(s.get("created_at") or ""),
    }


def _normalize_template(t: dict) -> TemplateDict:
    return {
        "id": int(t.get("id") or 0),
        "name": str(t.get("name") or ""),
        "subject": str(t.get("subject") or ""),
        "body": str(t.get("body") or ""),
        "created_at": str(t.get("created_at") or ""),
    }


class MastersState(rx.State):
    """CRUD state for Company Profile, Products, Target Audience, Email Templates."""

    # ── Company profile ────────────────────────────────────────────────────────
    company_id: int = 0
    cp_company_name: str = ""
    cp_industry: str = ""
    cp_website: str = ""
    cp_description: str = ""
    cp_saved: bool = False

    # ── Products ───────────────────────────────────────────────────────────────
    products: list[ProductDict] = []
    show_add_product_modal: bool = False
    show_edit_product_modal: bool = False
    edit_product_id: int = 0
    prod_name: str = ""
    prod_description: str = ""

    # ── Target audience ────────────────────────────────────────────────────────
    ta_product_id: int = 0
    target_audiences: list[TargetAudienceDict] = []
    show_add_ta_modal: bool = False
    show_edit_ta_modal: bool = False
    edit_ta_id: int = 0
    ta_industry: str = ""
    ta_location: str = ""
    ta_country: str = ""
    ta_business_type: str = "B2B"
    ta_roles: str = ""
    ta_company_sizes: list[str] = []
    ta_keywords: str = ""
    ta_competitors: str = ""

    # ── Email templates ────────────────────────────────────────────────────────
    templates: list[TemplateDict] = []
    show_add_template_modal: bool = False
    show_edit_template_modal: bool = False
    edit_template_id: int = 0
    tpl_name: str = ""
    tpl_subject: str = ""
    tpl_body: str = ""

    # ── Country Sources ────────────────────────────────────────────────────────
    country_sources: list[CountrySourceDict] = []
    cs_filter_country: str = ""
    show_add_cs_modal: bool = False
    show_edit_cs_modal: bool = False
    edit_cs_id: int = 0
    cs_country: str = ""
    cs_business_type: str = "Both"
    cs_url: str = ""

    # ── Active tab ─────────────────────────────────────────────────────────────
    active_tab: str = "company"

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_masters(self):
        self._load_company()
        self._load_templates()
        self._load_country_sources()

    def _load_company(self):
        profile = get_company_profile()
        if profile:
            self.company_id = profile["id"]
            self.cp_company_name = profile.get("company_name") or ""
            self.cp_industry = profile.get("industry") or ""
            self.cp_website = profile.get("website") or ""
            self.cp_description = profile.get("description") or ""
            raw = get_products(self.company_id)
            self.products = [_normalize_product(p) for p in raw]
            # Load TA for first product if available
            if self.products and not self.ta_product_id:
                self.ta_product_id = self.products[0]["id"]
                self._load_target_audiences()

    def _load_target_audiences(self):
        if not self.ta_product_id:
            self.target_audiences = []
            return
        raw = get_all_target_audiences(self.ta_product_id)
        self.target_audiences = [_normalize_ta(t) for t in raw]

    def _reset_ta_form(self):
        self.ta_industry = ""
        self.ta_location = ""
        self.ta_country = ""
        self.ta_business_type = "B2B"
        self.ta_roles = ""
        self.ta_company_sizes = []
        self.ta_keywords = ""
        self.ta_competitors = ""

    def _load_templates(self):
        raw = get_email_templates()
        self.templates = [_normalize_template(t) for t in raw]

    # ── Company profile save ───────────────────────────────────────────────────

    def save_company(self, form_data: dict):
        save_company_profile({
            "company_name": form_data.get("company_name", ""),
            "industry": form_data.get("industry", ""),
            "website": form_data.get("website", ""),
            "description": form_data.get("description", ""),
        })
        self._load_company()
        return rx.toast.success("Company profile saved.")

    # ── Products ───────────────────────────────────────────────────────────────

    def open_add_product(self):
        self.prod_name = ""
        self.prod_description = ""
        self.show_add_product_modal = True

    def close_add_product(self):
        self.show_add_product_modal = False

    def add_product(self, form_data: dict):
        name = form_data.get("product_name", "").strip()
        if not name:
            return rx.toast.error("Product name is required.")
        if not self.company_id:
            return rx.toast.error("Save Company Profile first.")
        save_product(self.company_id, name, form_data.get("description", ""))
        self.show_add_product_modal = False
        self._load_company()
        return rx.toast.success("Product added.")

    def open_edit_product(self, product_id: int):
        prod = next((p for p in self.products if p["id"] == product_id), None)
        if not prod:
            return
        self.edit_product_id = product_id
        self.prod_name = prod["product_name"]
        self.prod_description = prod["description"]
        self.show_edit_product_modal = True

    def close_edit_product(self):
        self.show_edit_product_modal = False

    def save_edit_product(self, form_data: dict):
        name = form_data.get("product_name", "").strip()
        desc = form_data.get("description", "")
        from database.sqlite_db import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE products SET product_name=?, description=? WHERE id=?",
            (name, desc, self.edit_product_id),
        )
        conn.commit()
        conn.close()
        self.show_edit_product_modal = False
        self._load_company()
        return rx.toast.success("Product updated.")

    def delete_product_confirm(self, product_id: int):
        delete_product(product_id)
        self._load_company()
        return rx.toast.success("Product deleted.")

    # ── Target Audience ────────────────────────────────────────────────────────

    def set_ta_product(self, product_name: str):
        prod = next((p for p in self.products if p["product_name"] == product_name), None)
        if prod:
            self.ta_product_id = prod["id"]
            self._load_target_audiences()

    def toggle_company_size(self, size: str, checked: bool):
        if checked:
            if size not in self.ta_company_sizes:
                self.ta_company_sizes = self.ta_company_sizes + [size]
        else:
            self.ta_company_sizes = [s for s in self.ta_company_sizes if s != size]

    def open_add_ta_modal(self):
        if not self.ta_product_id:
            return rx.toast.error("Select a product first.")
        self._reset_ta_form()
        self.show_add_ta_modal = True

    def close_add_ta_modal(self):
        self.show_add_ta_modal = False

    def set_show_add_ta_modal(self, val: bool):
        self.show_add_ta_modal = val

    def add_ta(self, form_data: dict):
        if not self.ta_product_id:
            return rx.toast.error("Select a product first.")
        form_data["company_size"] = ", ".join(self.ta_company_sizes)
        add_target_audience(self.ta_product_id, form_data)
        self.show_add_ta_modal = False
        self._load_target_audiences()
        return rx.toast.success("Target audience added.")

    def open_edit_ta_modal(self, ta_id: int):
        ta = next((t for t in self.target_audiences if t["id"] == ta_id), None)
        if not ta:
            return
        self.edit_ta_id = ta_id
        self.ta_industry = ta["industry"]
        self.ta_location = ta["location"]
        self.ta_country = ta["country"]
        self.ta_business_type = ta["business_type"]
        self.ta_roles = ta["roles"]
        self.ta_company_sizes = [s.strip() for s in ta["company_size"].split(",") if s.strip()]
        self.ta_keywords = ta["keywords"]
        self.ta_competitors = ta["competitors"]
        self.show_edit_ta_modal = True

    def close_edit_ta_modal(self):
        self.show_edit_ta_modal = False

    def set_show_edit_ta_modal(self, val: bool):
        self.show_edit_ta_modal = val

    def save_edit_ta(self, form_data: dict):
        form_data["company_size"] = ", ".join(self.ta_company_sizes)
        update_target_audience(self.edit_ta_id, form_data)
        self.show_edit_ta_modal = False
        self._load_target_audiences()
        return rx.toast.success("Target audience updated.")

    def delete_ta(self, ta_id: int):
        delete_target_audience(ta_id)
        self._load_target_audiences()
        return rx.toast.success("Target audience deleted.")

    # ── Email Templates ────────────────────────────────────────────────────────

    def open_add_template(self):
        self.tpl_name = ""
        self.tpl_subject = ""
        self.tpl_body = ""
        self.show_add_template_modal = True

    def close_add_template(self):
        self.show_add_template_modal = False

    def add_template(self, form_data: dict):
        name = form_data.get("name", "").strip()
        subject = form_data.get("subject", "").strip()
        body = form_data.get("body", "").strip()
        if not name or not subject or not body:
            return rx.toast.error("All fields are required.")
        save_email_template(name, subject, body)
        self.show_add_template_modal = False
        self._load_templates()
        return rx.toast.success("Template created.")

    def open_edit_template(self, template_id: int):
        tpl = get_email_template_by_id(template_id)
        if not tpl:
            return
        self.edit_template_id = template_id
        self.tpl_name = tpl.get("name") or ""
        self.tpl_subject = tpl.get("subject") or ""
        self.tpl_body = tpl.get("body") or ""
        self.show_edit_template_modal = True

    def close_edit_template(self):
        self.show_edit_template_modal = False

    def save_edit_template(self, form_data: dict):
        name = form_data.get("name", "").strip()
        subject = form_data.get("subject", "").strip()
        body = form_data.get("body", "").strip()
        if not name or not subject or not body:
            return rx.toast.error("All fields are required.")
        save_email_template(name, subject, body, template_id=self.edit_template_id)
        self.show_edit_template_modal = False
        self._load_templates()
        return rx.toast.success("Template updated.")

    def delete_template_confirm(self, template_id: int):
        delete_email_template(template_id)
        self._load_templates()
        return rx.toast.success("Template deleted.")

    # ── Country Sources ────────────────────────────────────────────────────────

    def _load_country_sources(self):
        raw = get_all_country_sources()
        self.country_sources = [_normalize_country_source(s) for s in raw]

    def set_cs_filter_country(self, val: str):
        self.cs_filter_country = val

    def open_add_cs_modal(self):
        self.cs_country = ""
        self.cs_business_type = "Both"
        self.cs_url = ""
        self.show_add_cs_modal = True

    def close_add_cs_modal(self):
        self.show_add_cs_modal = False

    def set_show_add_cs_modal(self, val: bool):
        self.show_add_cs_modal = val

    def add_cs(self, form_data: dict):
        country = form_data.get("country", "").strip()
        url = form_data.get("url", "").strip()
        btype = form_data.get("business_type", "Both")
        if not country or not url:
            return rx.toast.error("Country and URL are required.")
        ok = add_country_source(country, btype, url)
        if not ok:
            return rx.toast.error("URL already exists for this country.")
        self.show_add_cs_modal = False
        self._load_country_sources()
        return rx.toast.success("Source added.")

    def open_edit_cs_modal(self, source_id: int):
        src = next((s for s in self.country_sources if s["id"] == source_id), None)
        if not src:
            return
        self.edit_cs_id = source_id
        self.cs_country = src["country"]
        self.cs_business_type = src["business_type"]
        self.cs_url = src["url"]
        self.show_edit_cs_modal = True

    def close_edit_cs_modal(self):
        self.show_edit_cs_modal = False

    def set_show_edit_cs_modal(self, val: bool):
        self.show_edit_cs_modal = val

    def save_edit_cs(self, form_data: dict):
        country = form_data.get("country", "").strip()
        url = form_data.get("url", "").strip()
        btype = form_data.get("business_type", "Both")
        if not country or not url:
            return rx.toast.error("Country and URL are required.")
        update_country_source(self.edit_cs_id, country, btype, url)
        self.show_edit_cs_modal = False
        self._load_country_sources()
        return rx.toast.success("Source updated.")

    def toggle_cs(self, source_id: int, current_active: int):
        toggle_country_source(source_id, not bool(current_active))
        self._load_country_sources()

    def delete_cs(self, source_id: int):
        delete_country_source(source_id)
        self._load_country_sources()
        return rx.toast.success("Source deleted.")

    # ── Tab ────────────────────────────────────────────────────────────────────

    def set_tab(self, tab: str):
        self.active_tab = tab

    # ── Computed ────────────────────────────────────────────────────────────────

    @rx.var
    def product_names_ta(self) -> list[str]:
        return [p["product_name"] for p in self.products if p["product_name"]]

    @rx.var
    def filtered_country_sources(self) -> list[CountrySourceDict]:
        if not self.cs_filter_country:
            return self.country_sources
        f = self.cs_filter_country.lower()
        return [s for s in self.country_sources if f in s["country"].lower()]

    @rx.var
    def cs_country_options(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for s in self.country_sources:
            if s["country"] and s["country"] not in seen:
                seen.add(s["country"])
                out.append(s["country"])
        return sorted(out)
