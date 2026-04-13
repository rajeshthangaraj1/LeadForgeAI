import reflex as rx
import sys, os, asyncio
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leadforge_ui.state.auth import AuthState
from database.sqlite_db import (
    get_products,
    get_company_profile,
    get_recent_logs,
    get_logs_for_run,
    get_agent_runs,
    delete_agent_run,
    clear_agent_logs,
)

PIPELINE_AGENTS = [
    "PlannerAgent", "QueryAgent", "SearchAgent", "ScraperAgent",
    "ExtractorAgent", "CleanerAgent", "EnrichAgent", "DBAgent", "ReporterAgent",
]
_PIPELINE_AGENT_SET = set(PIPELINE_AGENTS)


class ProductRef(TypedDict):
    id: int
    product_name: str
    description: str
    created_at: str


class RecentRun(TypedDict):
    id: int
    run_time: str
    status: str
    leads_found: int
    mode: str
    notes: str


class AgentProgressItem(TypedDict):
    name: str
    status: str  # "pending" | "running" | "done"


def _normalize_run(r: dict) -> RecentRun:
    return {
        "id": int(r.get("id") or 0),
        "run_time": str(r.get("run_time") or ""),
        "status": str(r.get("status") or ""),
        "leads_found": int(r.get("leads_found") or 0),
        "mode": str(r.get("mode") or ""),
        "notes": str(r.get("notes") or ""),
    }


class LeadGeneratorState(AuthState):
    """State for the Lead Generator page — pipeline runner + log viewer."""

    products: list[ProductRef] = []
    selected_product_id: int = 0
    selected_product_name: str = ""
    run_mode: str = "start"

    is_running: bool = False
    run_logs: list[str] = []
    run_result: dict = {}
    run_error: str = ""
    current_run_id: int = 0

    recent_runs: list[RecentRun] = []

    # ── Delete confirm ─────────────────────────────────────────────────────────
    show_delete_run_confirm: bool = False
    delete_run_id: int = 0

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_page(self):
        profile = get_company_profile(self.user_id)
        if profile:
            raw = get_products(profile["id"])
            self.products = [
                {
                    "id": int(p.get("id") or 0),
                    "product_name": str(p.get("product_name") or ""),
                    "description": str(p.get("description") or ""),
                    "created_at": str(p.get("created_at") or ""),
                }
                for p in raw
            ]
            if self.products and not self.selected_product_id:
                self.selected_product_id = self.products[0]["id"]
                self.selected_product_name = self.products[0]["product_name"]
        runs = get_agent_runs(user_id=self.user_id)
        self.recent_runs = [_normalize_run(r) for r in runs[:15]]

    # ── Controls ───────────────────────────────────────────────────────────────

    def set_product(self, val: str):
        try:
            self.selected_product_id = int(val)
        except (ValueError, TypeError):
            pass

    def set_product_by_name(self, name: str):
        for p in self.products:
            if p["product_name"] == name:
                self.selected_product_id = p["id"]
                self.selected_product_name = name
                return

    def set_run_mode(self, val: str):
        self.run_mode = val

    # ── Pipeline ───────────────────────────────────────────────────────────────

    def start_pipeline(self):
        if not self.selected_product_id:
            return rx.toast.error("Select a product first.")
        return LeadGeneratorState.run_pipeline_bg

    @rx.event(background=True)
    async def run_pipeline_bg(self):
        async with self:
            if self.is_running:
                return
            product_id = self.selected_product_id
            mode = self.run_mode
            _uid = self.user_id
            self.is_running = True
            self.run_logs = ["[LeadForge] Pipeline starting…"]
            self.run_result = {}
            self.run_error = ""
            self.current_run_id = 0

        try:
            loop = asyncio.get_event_loop()

            def _run():
                from pipeline.run_pipeline import run_pipeline
                return run_pipeline(product_id, mode, user_id=_uid)

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(executor, _run)

                # Wait briefly then detect run_id from DB
                await asyncio.sleep(2)
                runs = get_agent_runs(product_id=product_id, user_id=_uid)
                run_id = runs[0]["id"] if runs else 0
                async with self:
                    self.current_run_id = run_id

                # Poll logs every 3 seconds while running
                while not future.done():
                    await asyncio.sleep(3)
                    logs = get_logs_for_run(run_id) if run_id else get_recent_logs(limit=100)
                    async with self:
                        self.run_logs = [
                            f"[{l['agent_name']}] {l['message']}"
                            for l in logs
                        ]

                result = await future

            async with self:
                self.run_result = result or {}
                final_run_id = result.get("run_id", run_id) if result else run_id
                self.current_run_id = final_run_id
                runs = get_agent_runs(user_id=_uid)
                self.recent_runs = [_normalize_run(r) for r in runs[:15]]
                logs = get_logs_for_run(final_run_id) if final_run_id else get_recent_logs(limit=200)
                self.run_logs = [
                    f"[{l['agent_name']}] {l['message']}"
                    for l in logs
                ]

        except Exception as exc:
            async with self:
                self.run_error = str(exc)

        finally:
            async with self:
                self.is_running = False

    def stop_pipeline(self):
        self.is_running = False
        return rx.toast.info("Stop requested — current step will finish.")

    # ── Delete run ─────────────────────────────────────────────────────────────

    def open_delete_run_confirm(self, run_id: int):
        self.delete_run_id = run_id
        self.show_delete_run_confirm = True

    def cancel_delete_run(self):
        self.show_delete_run_confirm = False

    def confirm_delete_run(self):
        delete_agent_run(self.delete_run_id)
        self.show_delete_run_confirm = False
        runs = get_agent_runs(user_id=self.user_id)
        self.recent_runs = [_normalize_run(r) for r in runs[:15]]
        return rx.toast.success("Pipeline run deleted.")

    def set_show_delete_run_confirm(self, val: bool):
        self.show_delete_run_confirm = val

    # ── Clear logs ─────────────────────────────────────────────────────────────

    def clear_logs(self):
        clear_agent_logs()
        self.logs = []
        return rx.toast.success("Agent logs cleared.")

    # ── Computed ────────────────────────────────────────────────────────────────

    @rx.var
    def product_options(self) -> list[tuple[str, str]]:
        return [(str(p["id"]), p["product_name"]) for p in self.products]

    @rx.var
    def product_names(self) -> list[str]:
        return [p["product_name"] for p in self.products if p["product_name"]]

    @rx.var
    def run_summary_lines(self) -> list[str]:
        if not self.run_result:
            return []
        r = self.run_result
        return [
            f"Status: {r.get('status', 'N/A')}",
            f"Leads found: {r.get('leads_found', 0)}",
            f"Summary: {r.get('summary', '')}",
        ]

    @rx.var
    def agent_progress(self) -> list[AgentProgressItem]:
        """Derive per-agent status from current run_logs."""
        seen: set[str] = set()
        for line in self.run_logs:
            if line.startswith("["):
                try:
                    agent = line[1:line.index("]")]
                    if agent in _PIPELINE_AGENT_SET:
                        seen.add(agent)
                except ValueError:
                    pass

        # Find index of last agent seen in pipeline order
        last_idx = -1
        for i, a in enumerate(PIPELINE_AGENTS):
            if a in seen:
                last_idx = i

        result: list[AgentProgressItem] = []
        for i, name in enumerate(PIPELINE_AGENTS):
            if i < last_idx:
                status = "done"
            elif i == last_idx:
                status = "running" if self.is_running else "done"
            else:
                status = "pending"
            result.append({"name": name, "status": status})
        return result
