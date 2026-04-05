# LeadForge AI — Product Overview

**For:** Internal team
**Status:** Phases 1, 2, and 3 complete and working

---

## What Is LeadForge AI?

LeadForge AI is an AI-powered lead generation and email outreach platform that we built entirely in-house. It automatically finds potential business customers (B2B or B2C leads) from the internet, extracts their contact details, enriches the data, and lets you run email campaigns — all from a web dashboard running on your own machine.

**The key difference from tools like Apollo.io, Clay, or Lemlist:** everything runs locally. No monthly subscription. No data sent to any third-party cloud. No API costs for the core pipeline. Your leads stay on your machine.

---

## The Problem It Solves

Finding leads manually is slow and expensive:
- Searching Google, directories, Maps one by one takes hours per day
- Paid tools like Apollo.io cost $100–500/month and still require manual work
- Exported lists go stale quickly
- Following up on replies requires switching between Gmail, spreadsheets, and CRM

LeadForge AI automates the entire loop: **search → scrape → extract → enrich → email → reply tracking**, in one dashboard.

---

## How It Works — The Pipeline

When you click "Start Lead Generation" for a product, 9 AI agents run in sequence:

```
1. Planner      Reads your target audience settings and uses AI to build
                a focused strategy (ICP — Ideal Customer Profile)

2. Query        AI generates 12 smart search queries tailored to your
                industry, country, and B2B/B2C type

3. Search       Runs those queries across multiple sources:
                  • DuckDuckGo (free web search)
                  • Google Maps (gets phone + address directly)
                  • Country business directories (80+ pre-configured)
                  • Optional paid APIs: Brave, Serper, SerpAPI

4. Scraper      Opens each URL in a headless browser, waits for JavaScript
                to render, extracts the text. Also checks /contact and
                /about pages for phone numbers. Skips PDFs, images, forums.
                Retries once on failure.

5. Extractor    AI reads each scraped page and pulls out:
                  name, company, role, email, phone, LinkedIn

6. Cleaner      Fixes formatting, removes duplicates, scores each lead
                0-10 based on how much contact info they have

7. Enricher     AI adds: industry sector, company size estimate,
                B2B or B2C classification
                (Skips this for leads that already have full data)

8. DB Agent     Drops leads with no email AND no phone (useless)
                Skips leads already saved from a previous run
                Saves the rest to the database with quality score

9. Reporter     AI writes a short executive summary of what was found
```

The whole run typically takes 5–15 minutes depending on the number of URLs and the AI model speed.

---

## What We Built — Feature by Feature

### Phase 1: Lead Generation (Complete)

**Company & Product Setup**
- Define your company profile once
- Add multiple products (e.g. WMS Software, ERP System, CRM Tool)
- Each product has its own target audience configuration:
  - Industry, location, country
  - B2B / B2C / Both
  - Job roles to target (e.g. "Operations Manager, Logistics Head")
  - Company size (1-10, 11-50, 51-200, etc.)
  - Keywords and competitors to focus on

**Search Sources**
- DuckDuckGo — free, always available
- Google Maps — returns business name, phone, address directly without needing to scrape websites
- 80+ business directories across 13 countries (UAE, India, Saudi Arabia, USA, UK, Australia, Qatar, Kuwait, Bahrain, Oman, Singapore, Germany, Canada)
- Optional paid providers: Brave Search, Serper.dev, SerpAPI — add API key in the UI, no code changes

**Lead Quality**
- Every lead gets a quality score (0–10):
  - +3 if email is present
  - +2 if phone is present
  - +2 if company name is present
  - +1 each for name, industry, LinkedIn
- Leads with no email AND no phone are dropped before saving
- Same lead from previous runs is not saved again (cross-run deduplication)

**Dashboard**
- View all leads with filters: industry, location, pipeline stage, search
- See quality score and stage for every lead
- Export to CSV
- Charts: leads by industry, location, pipeline stage
- Edit pipeline stage + add notes per lead

### Phase 2: Email Outreach (Complete)

**Templates**
- Create reusable email templates with personalisation placeholders:
  `{name}`, `{first_name}`, `{company}`, `{role}`, `{industry}`, `{location}`
- Preview template with real lead data before sending

**Campaigns**
- Create a campaign: pick a product, pick a template
- Select which leads to include (filtered by industry, stage, etc.)
- Preview the first email before sending
- Send in bulk — one email per lead, personalised
- Gmail App Password used — no OAuth, no Google Cloud setup needed

**Reply Monitoring**
- Connects to Gmail inbox via IMAP
- Matches incoming replies to the original sent email using Message-ID headers
- Fallback: if Message-ID wasn't stored (older sends), matches by sender email address
- Auto-reply detection: filters out-of-office / vacation messages automatically
- AI sentiment classification of real replies:
  - Interested (shown in green)
  - Not Interested (shown in red)
  - Needs Info (shown in yellow)
  - Other / Out Of Office (shown in grey)

**Campaign Analytics**
- Per-campaign stats: total sent, delivered, replied, auto-replies
- Reply rate % calculated and displayed
- Full send history per campaign

### Phase 3: Lead Management (Complete)

**Pipeline Stages**
- Every lead moves through stages: New → Contacted → Replied → Qualified → Won / Lost
- Filter dashboard by stage to see exactly where each lead is
- Update stage from the dashboard in one click

**Notes**
- Add free-text notes per lead (call outcomes, next steps, etc.)

**CSV Import**
- Upload leads from an external CSV file
- Map columns to our fields (name, company, email, phone, etc.)
- Assign imported leads to a product

---

## What the AI Does (And Doesn't Do)

| AI Task | Agent | Model |
|---|---|---|
| Build targeting strategy + ICP | Planner | Ollama LLM |
| Generate search queries | Query | Ollama LLM |
| Extract contacts from web page text | Extractor | Ollama LLM |
| Enrich industry / company size / type | Enrich | Ollama LLM |
| Write executive run summary | Reporter | Ollama LLM |
| Classify reply sentiment | Reply Monitor | Ollama LLM |

**The AI does NOT:**
- Search the web directly (that's done by the Search agent using real APIs/scraping)
- Verify that email addresses actually exist and receive mail
- Guarantee accuracy of extracted data — it reads web page text and makes its best guess

The AI model runs locally via **Ollama**. Default model: `qwen3:8b`. No data leaves your machine.

---

## Technology Stack (Summary)

| What | Tool | Why |
|---|---|---|
| Dashboard | Reflex (Python full-stack) | Python-only, reactive web UI, no JS needed |
| AI orchestration | LangGraph | Manages the 9-agent pipeline as a state machine |
| Local AI | Ollama + qwen3:8b | Free, runs on GPU, no API costs |
| Web scraping | Playwright | Handles JavaScript-heavy pages |
| Database | SQLite | Simple, local, no server needed |
| Email send | Python smtplib (Gmail) | No external service needed |
| Email receive | Python imaplib (Gmail) | Standard IMAP protocol |

---

## Comparison With Paid Tools

| Feature | LeadForge AI | Apollo.io | Clay.com | Lemlist | Instantly |
|---|---|---|---|---|---|
| Lead search & scraping | Yes | Yes | Yes | No | No |
| AI-powered extraction | Yes (local) | No | Yes (cloud) | No | No |
| Google Maps data | Yes | No | No | No | No |
| Country directories | Yes (80+) | No | No | No | No |
| Runs offline / local | Yes | No | No | No | No |
| Email campaigns | Yes | Yes | Yes | Yes | Yes |
| Reply monitoring | Yes | Yes | Yes | Yes | Yes |
| AI reply sentiment | Yes | No | No | No | No |
| Lead pipeline stages | Yes | Yes | Yes | Yes | Yes |
| Monthly cost | $0 | $99–$599 | $149–$800 | $39–$159 | $37–$358 |

---

## What's Planned Next

### High Priority
- **Email sequences (drip campaigns):** Automatically send a follow-up email if no reply after N days. Single email gets ~8% reply rate; a 3-step sequence gets 25–30%.
- **AI personalised opener:** Use AI to write a custom 1-sentence opening line per lead based on their company and industry.
- **Job board scraping:** Scrape LinkedIn Jobs and Indeed to find companies actively hiring — these are warm leads (they have budget, they're growing).

### Medium Priority
- **Concurrent scraping:** Currently scrapes one URL at a time. Parallelising would make the pipeline 5–10x faster.
- **Domain email finder:** Given a company website (company.com), find likely email patterns (first.last@company.com).
- **Scheduled pipeline runs:** Auto-run every Monday morning without clicking Start.

### Lower Priority
- **Google Sheets export:** Direct sync instead of CSV download.
- **REST API:** Allow other tools or scripts to trigger pipeline runs or fetch leads programmatically.
- **Multi-user access:** Role-based login (admin vs read-only viewer).

---

## How to Run It

```bash
# Clone the repo and enter the folder
cd LeadForgeAI

# Create virtual environment
python3 -m venv leadforge_env
source leadforge_env/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Pull the AI model (one time)
ollama pull qwen3:8b

# Start the app
reflex run
```

Open browser at `http://localhost:3000`
Login: `admin` / `admin`

**First-time setup in the app:**
1. Go to Masters → Company Profile → add your company and products
2. Go to Masters → Target Audience → configure target per product
3. Go to Lead Generator → select a product → click Start Lead Generation
4. After leads are collected, go to Masters → Email Templates → create a template
5. Go to Email Campaigns → create a campaign → send

---

## Files You Should Know About

| File | What it is |
|---|---|
| `leadforge_ui/leadforge_ui.py` | App entry point — registers all pages |
| `leadforge_ui/pages/` | One file per page/route |
| `leadforge_ui/state/` | One rx.State class per page — all event handlers and DB calls |
| `config/settings.py` | Change model name, timeouts, login credentials here |
| `database/sqlite_db.py` | All database tables, queries, and seed data |
| `agents/` | One file per pipeline agent |
| `graph/agent_graph.py` | The pipeline wiring (which agent runs after which) |
| `utils/llm_utils.py` | How we call Ollama — shared by all agents |
| `utils/email_utils.py` | Gmail send + IMAP reply fetch logic |
| `leadforge.db` | The SQLite database — not committed to git |

---

*Built by Rajesh's team. For setup, see README.md. For pipeline details, check the Agent Logs page inside the app.*
