import reflex as rx
import sys, os, csv, io
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.sqlite_db import (
    get_all_leads,
    update_lead_stage,
    update_lead_notes,
    get_connection,
    get_company_profile,
)

_EXPORT_FIELDS = ["name", "company", "role", "email", "phone", "linkedin",
                  "industry", "location", "stage", "score", "notes", "created_at"]
_IMPORT_FIELDS = ["name", "company", "role", "email", "phone", "linkedin",
                  "industry", "location"]


class LeadDict(TypedDict):
    id: int
    product_id: int
    name: str
    company: str
    role: str
    email: str
    phone: str
    linkedin: str
    industry: str
    location: str
    source: str
    stage: str
    score: int
    notes: str
    created_at: str


class PagedLeadRow(TypedDict):
    """LeadDict + a `selected` bool — used in rx.foreach rows."""
    id: int
    product_id: int
    name: str
    company: str
    role: str
    email: str
    phone: str
    linkedin: str
    industry: str
    location: str
    source: str
    stage: str
    score: int
    notes: str
    created_at: str
    selected: bool


def _normalize_lead(l: dict) -> LeadDict:
    return {
        "id": int(l.get("id") or 0),
        "product_id": int(l.get("product_id") or 0),
        "name": str(l.get("name") or ""),
        "company": str(l.get("company") or ""),
        "role": str(l.get("role") or ""),
        "email": str(l.get("email") or ""),
        "phone": str(l.get("phone") or ""),
        "linkedin": str(l.get("linkedin") or ""),
        "industry": str(l.get("industry") or ""),
        "location": str(l.get("location") or ""),
        "source": str(l.get("source") or ""),
        "stage": str(l.get("stage") or "new"),
        "score": int(l.get("score") or 0),
        "notes": str(l.get("notes") or ""),
        "created_at": str(l.get("created_at") or ""),
    }


def _score_lead(row: dict) -> int:
    score = 0
    if row.get("email"):    score += 3
    if row.get("phone"):    score += 2
    if row.get("company"):  score += 2
    if row.get("name"):     score += 1
    if row.get("industry"): score += 1
    if row.get("linkedin"): score += 1
    return min(score, 10)


def _upsert_lead(row: dict, product_id: int):
    """Insert a lead from CSV. Update if email OR phone already exists for this product."""
    email = (row.get("email") or "").strip().lower()
    phone = (row.get("phone") or "").strip()
    conn = get_connection()
    existing = None
    if email:
        existing = conn.execute(
            "SELECT id FROM leads WHERE product_id=? AND email=? LIMIT 1",
            (product_id, email),
        ).fetchone()
    if not existing and phone:
        existing = conn.execute(
            "SELECT id FROM leads WHERE product_id=? AND phone=? AND phone!='' LIMIT 1",
            (product_id, phone),
        ).fetchone()
    if existing:
        conn.execute(
            """UPDATE leads SET name=?, company=?, role=?, phone=?, linkedin=?,
               industry=?, location=?, stage=?, notes=?, score=? WHERE id=?""",
            (
                row.get("name", ""), row.get("company", ""), row.get("role", ""),
                phone, row.get("linkedin", ""), row.get("industry", ""),
                row.get("location", ""), row.get("stage", "new") or "new",
                row.get("notes", ""), _score_lead(row), existing["id"],
            ),
        )
        conn.commit()
        conn.close()
        return "updated"
    else:
        conn.execute(
            """INSERT INTO leads (product_id, name, company, role, email, phone, linkedin,
               industry, location, stage, notes, score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                product_id,
                row.get("name", ""), row.get("company", ""), row.get("role", ""),
                email, phone, row.get("linkedin", ""),
                row.get("industry", ""), row.get("location", ""),
                row.get("stage", "new") or "new", row.get("notes", ""),
                _score_lead(row),
            ),
        )
        conn.commit()
        conn.close()
        return "inserted"


def _delete_lead(lead_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
    conn.commit()
    conn.close()


def _bulk_delete_leads(lead_ids: list[int]):
    if not lead_ids:
        return
    conn = get_connection()
    placeholders = ",".join("?" * len(lead_ids))
    conn.execute(f"DELETE FROM leads WHERE id IN ({placeholders})", lead_ids)
    conn.commit()
    conn.close()


def _update_lead(lead_id: int, data: dict):
    fields = {
        k: data.get(k, "")
        for k in ("name", "company", "role", "email", "phone", "linkedin", "industry", "location")
    }
    conn = get_connection()
    conn.execute(
        """UPDATE leads SET name=:name, company=:company, role=:role,
           email=:email, phone=:phone, linkedin=:linkedin,
           industry=:industry, location=:location WHERE id=:id""",
        {**fields, "id": lead_id},
    )
    conn.commit()
    conn.close()


class LeadsState(rx.State):
    """Full CRUD state for the Leads Management page."""

    leads: list[LeadDict] = []
    filtered_leads: list[LeadDict] = []

    # ── Filters ────────────────────────────────────────────────────────────────
    filter_industry: str = ""
    filter_location: str = ""
    filter_stage: str = ""
    search_query: str = ""

    # ── Edit modal ─────────────────────────────────────────────────────────────
    show_edit_modal: bool = False
    edit_lead_id: int = 0
    edit_name: str = ""
    edit_company: str = ""
    edit_role: str = ""
    edit_email: str = ""
    edit_phone: str = ""
    edit_linkedin: str = ""
    edit_industry: str = ""
    edit_location: str = ""
    edit_notes: str = ""
    edit_stage: str = "New"

    # ── Delete confirm ─────────────────────────────────────────────────────────
    show_delete_confirm: bool = False
    delete_lead_id: int = 0
    delete_lead_name: str = ""

    # ── Bulk selection ─────────────────────────────────────────────────────────
    selected_lead_ids: list[int] = []
    show_bulk_delete_confirm: bool = False

    # ── Toast msg ──────────────────────────────────────────────────────────────
    toast_msg: str = ""

    # ── Pagination ─────────────────────────────────────────────────────────────
    page: int = 1
    page_size: int = 20

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_leads(self):
        raw = get_all_leads()
        self.leads = [_normalize_lead(l) for l in raw]
        self._apply_filters()

    # ── Filters ────────────────────────────────────────────────────────────────

    def set_filter_industry(self, val: str):
        self.filter_industry = val
        self.page = 1
        self._apply_filters()

    def set_filter_location(self, val: str):
        self.filter_location = val
        self.page = 1
        self._apply_filters()

    def set_filter_stage(self, val: str):
        self.filter_stage = val
        self.page = 1
        self._apply_filters()

    def set_search_query(self, val: str):
        self.search_query = val
        self.page = 1
        self._apply_filters()

    def clear_filters(self):
        self.filter_industry = ""
        self.filter_location = ""
        self.filter_stage = ""
        self.search_query = ""
        self.page = 1
        self._apply_filters()

    def _apply_filters(self):
        result = self.leads
        if self.filter_industry:
            result = [l for l in result if self.filter_industry.lower() in l["industry"].lower()]
        if self.filter_location:
            result = [l for l in result if self.filter_location.lower() in l["location"].lower()]
        if self.filter_stage:
            result = [l for l in result if l["stage"].lower() == self.filter_stage.lower()]
        if self.search_query:
            q = self.search_query.lower()
            result = [
                l for l in result
                if q in l["name"].lower()
                or q in l["company"].lower()
                or q in l["email"].lower()
            ]
        self.filtered_leads = result

    # ── Pagination ─────────────────────────────────────────────────────────────

    @rx.var
    def paged_leads(self) -> list[LeadDict]:
        start = (self.page - 1) * self.page_size
        return self.filtered_leads[start : start + self.page_size]

    @rx.var
    def paged_leads_with_sel(self) -> list[PagedLeadRow]:
        """Paged leads with a `selected` bool embedded — used by rx.foreach rows."""
        sel = set(self.selected_lead_ids)
        start = (self.page - 1) * self.page_size
        page = self.filtered_leads[start : start + self.page_size]
        return [
            {
                "id": l["id"], "product_id": l["product_id"],
                "name": l["name"], "company": l["company"], "role": l["role"],
                "email": l["email"], "phone": l["phone"], "linkedin": l["linkedin"],
                "industry": l["industry"], "location": l["location"],
                "source": l["source"], "stage": l["stage"],
                "score": l["score"], "notes": l["notes"],
                "created_at": l["created_at"],
                "selected": l["id"] in sel,
            }
            for l in page
        ]

    @rx.var
    def total_pages(self) -> int:
        return max(1, (len(self.filtered_leads) + self.page_size - 1) // self.page_size)

    @rx.var
    def leads_count_label(self) -> str:
        return f"{len(self.filtered_leads)} leads"

    def prev_page(self):
        if self.page > 1:
            self.page -= 1

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1

    # ── Bulk selection ─────────────────────────────────────────────────────────

    @rx.var
    def selection_count(self) -> int:
        return len(self.selected_lead_ids)

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_lead_ids) > 0

    @rx.var
    def all_page_selected(self) -> bool:
        page = self.paged_leads
        if not page:
            return False
        sel = set(self.selected_lead_ids)
        return all(l["id"] in sel for l in page)

    @rx.var
    def all_filtered_selected(self) -> bool:
        if not self.filtered_leads:
            return False
        sel = set(self.selected_lead_ids)
        return all(l["id"] in sel for l in self.filtered_leads)

    def toggle_lead_selection(self, lead_id: int, checked: bool):
        if checked:
            if lead_id not in self.selected_lead_ids:
                self.selected_lead_ids = self.selected_lead_ids + [lead_id]
        else:
            self.selected_lead_ids = [i for i in self.selected_lead_ids if i != lead_id]

    def toggle_all_page(self, checked: bool):
        page_ids = [l["id"] for l in self.paged_leads]
        current = set(self.selected_lead_ids)
        if checked:
            self.selected_lead_ids = list(current | set(page_ids))
        else:
            self.selected_lead_ids = list(current - set(page_ids))

    def select_all_filtered(self):
        """Select every lead in the current filtered view (all pages)."""
        self.selected_lead_ids = [l["id"] for l in self.filtered_leads]

    def clear_selection(self):
        self.selected_lead_ids = []

    def open_bulk_delete_confirm(self):
        if self.selected_lead_ids:
            self.show_bulk_delete_confirm = True

    def cancel_bulk_delete(self):
        self.show_bulk_delete_confirm = False

    def set_show_bulk_delete_confirm(self, val: bool):
        self.show_bulk_delete_confirm = val

    def confirm_bulk_delete(self):
        count = len(self.selected_lead_ids)
        _bulk_delete_leads(list(self.selected_lead_ids))
        self.selected_lead_ids = []
        self.show_bulk_delete_confirm = False
        self.load_leads()
        return rx.toast.success(f"Deleted {count} lead(s).")

    # ── Stage inline update ────────────────────────────────────────────────────

    def update_stage(self, lead_id: int, stage: str):
        update_lead_stage(lead_id, stage)
        self.load_leads()

    # ── Edit modal ─────────────────────────────────────────────────────────────

    def open_edit_modal(self, lead_id: int):
        lead = next((l for l in self.leads if l["id"] == lead_id), None)
        if not lead:
            return
        self.edit_lead_id = lead_id
        self.edit_name = lead["name"]
        self.edit_company = lead["company"]
        self.edit_role = lead["role"]
        self.edit_email = lead["email"]
        self.edit_phone = lead["phone"]
        self.edit_linkedin = lead["linkedin"]
        self.edit_industry = lead["industry"]
        self.edit_location = lead["location"]
        self.edit_notes = lead["notes"]
        self.edit_stage = lead["stage"].capitalize() if lead["stage"] else "New"
        self.show_edit_modal = True

    def close_edit_modal(self):
        self.show_edit_modal = False

    def save_edit_lead(self, form_data: dict):
        _update_lead(self.edit_lead_id, form_data)
        update_lead_notes(self.edit_lead_id, form_data.get("notes", ""))
        update_lead_stage(self.edit_lead_id, form_data.get("stage", "New"))
        self.show_edit_modal = False
        self.load_leads()
        return rx.toast.success("Lead updated.")

    # ── Delete ─────────────────────────────────────────────────────────────────

    def open_delete_confirm(self, lead_id: int, name: str):
        self.delete_lead_id = lead_id
        self.delete_lead_name = name or ""
        self.show_delete_confirm = True

    def set_show_edit_modal(self, val: bool):
        self.show_edit_modal = val

    def set_show_delete_confirm(self, val: bool):
        self.show_delete_confirm = val

    def cancel_delete(self):
        self.show_delete_confirm = False

    def confirm_delete(self):
        _delete_lead(self.delete_lead_id)
        self.show_delete_confirm = False
        self.load_leads()
        return rx.toast.success("Lead deleted.")

    # ── CSV Export ─────────────────────────────────────────────────────────────

    def export_leads_csv(self):
        """Build CSV in-memory and trigger browser download via data URI."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=_EXPORT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in self.filtered_leads:
            writer.writerow({k: lead.get(k, "") for k in _EXPORT_FIELDS})
        # UTF-8 BOM so Excel opens without garbled characters
        csv_bytes = output.getvalue().encode("utf-8-sig")
        return rx.download(
            data=csv_bytes,
            filename="leads_export.csv",
        )

    def download_sample_csv(self):
        """Download sample CSV with import headers + one example row."""
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=_IMPORT_FIELDS,
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerow({
            "name": "John Smith",
            "company": "Acme Corp",
            "role": "CEO",
            "email": "john@acme.com",
            "phone": "+1-555-0100",
            "linkedin": "https://linkedin.com/in/johnsmith",
            "industry": "Technology",
            "location": "New York, USA",
        })
        csv_bytes = output.getvalue().encode("utf-8-sig")
        return rx.download(
            data=csv_bytes,
            filename="leads_sample.csv",
        )

    # ── CSV Import ─────────────────────────────────────────────────────────────

    import_status: str = ""

    async def handle_csv_import(self, files: list[rx.UploadFile]):
        if not files:
            return rx.toast.error("No file selected.")
        file = files[0]
        content = await file.read()
        try:
            text = content.decode("utf-8-sig")  # handle BOM
        except Exception:
            text = content.decode("latin-1", errors="ignore")

        # Detect product_id
        profile = get_company_profile()
        product_id = None
        if profile:
            from database.sqlite_db import get_products
            prods = get_products(profile["id"])
            if prods:
                product_id = prods[0]["id"]

        if not product_id:
            self.import_status = "No product found — set up a product in Masters first."
            return rx.toast.error(self.import_status)

        reader = csv.DictReader(io.StringIO(text))
        inserted = updated = skipped = 0
        for row in reader:
            email = (row.get("email") or "").strip()
            phone = (row.get("phone") or "").strip()
            if not email and not phone:
                skipped += 1
                continue
            result = _upsert_lead(row, product_id)
            if result == "inserted":
                inserted += 1
            else:
                updated += 1

        self.import_status = f"Import done: {inserted} inserted, {updated} updated, {skipped} skipped (no email/phone)."
        self.load_leads()
        return rx.toast.success(self.import_status)

    # ── Computed filter options ─────────────────────────────────────────────────

    @rx.var
    def industry_options(self) -> list[str]:
        seen = set()
        out = []
        for l in self.leads:
            ind = l["industry"]
            if ind and ind not in seen:
                seen.add(ind)
                out.append(ind)
        return sorted(out)

    @rx.var
    def location_options(self) -> list[str]:
        seen = set()
        out = []
        for l in self.leads:
            loc = l["location"]
            if loc and loc not in seen:
                seen.add(loc)
                out.append(loc)
        return sorted(out)
