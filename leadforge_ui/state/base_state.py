import reflex as rx
import sys, os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.sqlite_db import (
    init_db,
    get_company_profile,
    get_products,
)


class ProductRef(TypedDict):
    id: int
    product_name: str
    description: str
    created_at: str


class AppState(rx.State):
    """Global shared state — company profile, product selector."""

    company_name: str = "LeadForge AI"
    products: list[ProductRef] = []
    selected_product_id: int = 0
    selected_product_name: str = "All Products"

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def on_app_load(self):
        init_db()
        self._load_products()

    def _load_products(self):
        profile = get_company_profile()
        if profile:
            self.company_name = profile.get("company_name", "LeadForge AI")
            prods = get_products(profile["id"])
            self.products = [
                {
                    "id": int(p.get("id") or 0),
                    "product_name": str(p.get("product_name") or ""),
                    "description": str(p.get("description") or ""),
                    "created_at": str(p.get("created_at") or ""),
                }
                for p in prods
            ]
            if self.products and self.selected_product_id == 0:
                self.selected_product_id = self.products[0]["id"]
                self.selected_product_name = self.products[0]["product_name"]

    # ── Product selector ───────────────────────────────────────────────────────

    def set_product(self, product_name: str):
        """Called by the header select — receives product_name, looks up its id."""
        for p in self.products:
            if p["product_name"] == product_name:
                self.selected_product_id = p["id"]
                self.selected_product_name = product_name
                return

    # ── Computed helpers ───────────────────────────────────────────────────────

    @rx.var
    def product_options(self) -> list[str]:
        return [str(p["id"]) for p in self.products]

    @rx.var
    def product_labels(self) -> list[str]:
        return [p["product_name"] for p in self.products if p["product_name"]]
