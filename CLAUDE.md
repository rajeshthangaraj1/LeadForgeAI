# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Activate the virtual environment first
source leadforge_env/bin/activate

# Start the Reflex dev server (frontend + backend)
reflex run

# Production export
reflex export --no-zip
```

App runs at `http://localhost:3000`. Default login: `admin` / `admin` (set in `config/settings.py`).

Ollama must be running locally (`ollama serve`) with a model pulled, e.g. `ollama pull qwen3:8b`.

## Architecture Overview

This is a **Reflex 0.8.x** app (Python full-stack framework). The entire UI lives in `leadforge_ui/`.

### Entry point
- `rxconfig.py` — Reflex config (`app_name="leadforge_ui"`)
- `leadforge_ui/leadforge_ui.py` — imports all pages to register them, creates `rx.App()`

### Layer map

```
leadforge_ui/
  pages/         One file per route — pure UI components, no business logic
  state/         One rx.State subclass per page — all event handlers + DB calls
  components/    Shared UI components (navbar, modals, etc.)
  styles/        Theme/style constants

agents/          LangGraph-based AI agents (planner, query, search, scraper, extractor, cleaner, enrich, db, reporter)
graph/           agent_graph.py — LangGraph StateGraph wiring the agent pipeline
pipeline/        run_pipeline.py — entry point called by LeadGeneratorState
database/        sqlite_db.py — all SQLite helpers + schema (init_db())
config/          settings.py — global constants (Ollama URL, model, limits, credentials)
utils/           llm_utils.py, email_utils.py, helpers.py
leadforge.db     SQLite database file (WAL mode)
```

### State / page pairing

| Page file | State class | Route |
|---|---|---|
| `login.py` | `AuthState` | `/login`, `/` |
| `register.py` | `AuthState` | `/register` |
| `dashboard.py` | `DashboardState` | `/dashboard` |
| `leads.py` | `LeadsState` | `/leads` |
| `lead_generator.py` | `LeadGeneratorState` | `/lead-generator` |
| `campaigns.py` | `CampaignsState` | `/campaigns` |
| `masters.py` | `MastersState` | `/masters` |
| `settings_page.py` | `SettingsState` | `/settings` |
| `analytics.py` | `AnalyticsState` | `/analytics` |

### Authentication pattern

`AuthState` (in `state/auth.py`) owns `is_authenticated`. Every protected page uses:

```python
@rx.page(route="/some-page", on_load=[AuthState.check_auth, XState.load_x])
```

`check_auth` runs first and redirects to `/login` if not authenticated. **Do not re-check auth inside other state load methods** — accessing `AuthState.is_authenticated` from a different state class raises `VarTypeError` in Reflex 0.8.x because cross-state var reads return a Reflex Var object, not a Python bool.

The index page (`/`) uses `on_load=AuthState.redirect_from_index` and returns a spinner component — never put `rx.redirect()` inside `rx.cond()`.

### Reflex-specific rules

- All state vars used in `rx.foreach` must have explicit **TypedDict** types.
- Computed vars (`@rx.var`) returning `list[str]` for `rx.select` must **filter out empty strings** — Radix UI rejects empty-string Select.Item values.
- Background event handlers use `@rx.event(background=True)` with `async with self:` to mutate state.
- The DB path is resolved relative to `database/sqlite_db.py` → `leadforge.db` at the project root.
- State files use `sys.path.insert(0, ...)` to allow importing from the project root (`database/`, `utils/`, `config/`).

### Agent pipeline flow

`LeadGeneratorState.run_pipeline()` → `pipeline/run_pipeline.py` → `graph/agent_graph.py` (LangGraph) → sequential agents:

`PlannerAgent` → `QueryAgent` → `SearchAgent` (multi-provider) → `ScraperAgent` (Playwright) → `ExtractorAgent` (LLM) → `CleanerAgent` → `EnrichAgent` (LLM) → `DBAgent` → `ReporterAgent`

### Database

Single SQLite file (`leadforge.db`, WAL mode). All schema is created by `init_db()` in `database/sqlite_db.py`. Key tables: `company_profile`, `products`, `target_audience`, `leads`, `email_templates`, `email_campaigns`, `email_sends`, `search_providers`, `gmail_config`, `agent_runs`, `agent_logs`.

### Changing the LLM model

Edit `OLLAMA_MODEL` in `config/settings.py` only — all agents read from there.
