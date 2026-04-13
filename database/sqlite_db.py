import sqlite3
import os
from datetime import datetime

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, "leadforge.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS company_profile (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            industry     TEXT,
            website      TEXT,
            description  TEXT,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            company_profile_id INTEGER NOT NULL,
            product_name       TEXT NOT NULL,
            description        TEXT,
            created_at         TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_profile_id) REFERENCES company_profile(id)
        );

        CREATE TABLE IF NOT EXISTS target_audience (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id    INTEGER NOT NULL,
            industry      TEXT,
            location      TEXT,
            country       TEXT,
            business_type TEXT DEFAULT 'B2B',
            roles         TEXT,
            company_size  TEXT,
            keywords      TEXT,
            competitors   TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS leads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name       TEXT,
            company    TEXT,
            role       TEXT,
            email      TEXT,
            phone      TEXT,
            linkedin   TEXT,
            industry   TEXT,
            location   TEXT,
            source     TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER,
            run_time    TEXT DEFAULT CURRENT_TIMESTAMP,
            mode        TEXT DEFAULT 'start',
            status      TEXT,
            leads_found INTEGER DEFAULT 0,
            notes       TEXT
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id     INTEGER,
            agent_name TEXT,
            message    TEXT,
            level      TEXT DEFAULT 'INFO',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS country_sources (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            country       TEXT NOT NULL,
            business_type TEXT NOT NULL DEFAULT 'Both',
            url           TEXT NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, url)
        );

        CREATE TABLE IF NOT EXISTS search_providers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL UNIQUE,
            display_name  TEXT NOT NULL,
            provider_type TEXT NOT NULL DEFAULT 'free',
            is_enabled    INTEGER NOT NULL DEFAULT 0,
            api_key       TEXT NOT NULL DEFAULT '',
            description   TEXT NOT NULL DEFAULT '',
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS gmail_config (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email        TEXT NOT NULL,
            app_password TEXT NOT NULL,
            smtp_host    TEXT NOT NULL DEFAULT 'smtp.gmail.com',
            smtp_port    INTEGER NOT NULL DEFAULT 587,
            imap_host    TEXT NOT NULL DEFAULT 'imap.gmail.com',
            imap_port    INTEGER NOT NULL DEFAULT 993,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_templates (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            subject    TEXT NOT NULL,
            body       TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_campaigns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            template_id INTEGER NOT NULL,
            product_id  INTEGER,
            status      TEXT DEFAULT 'draft',
            sent_count  INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES email_templates(id),
            FOREIGN KEY (product_id)  REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS email_sends (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id  INTEGER NOT NULL,
            lead_id      INTEGER NOT NULL,
            email_to     TEXT NOT NULL,
            subject      TEXT NOT NULL,
            status       TEXT DEFAULT 'sent',
            message_id   TEXT,
            sent_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            replied_at   TEXT,
            FOREIGN KEY (campaign_id) REFERENCES email_campaigns(id),
            FOREIGN KEY (lead_id)     REFERENCES leads(id)
        );
    """)

    # ── Safely add new columns to leads (ignored if already exist) ────────────
    _safe_add_column(cursor, "leads", "email_status",    "TEXT DEFAULT 'none'")
    _safe_add_column(cursor, "leads", "email_sent_at",   "TEXT")
    _safe_add_column(cursor, "leads", "email_replied_at","TEXT")
    _safe_add_column(cursor, "leads", "lead_source",     "TEXT DEFAULT 'pipeline'")
    # Phase 3 additions
    _safe_add_column(cursor, "leads", "score",  "INTEGER DEFAULT 0")
    _safe_add_column(cursor, "leads", "stage",  "TEXT DEFAULT 'new'")
    _safe_add_column(cursor, "leads", "notes",  "TEXT DEFAULT ''")
    # Phase 4: track which pipeline run created each lead
    _safe_add_column(cursor, "leads", "run_id", "INTEGER")

    # ── Multi-tenancy: user_id on all tenant-scoped tables ─────────────────
    _safe_add_column(cursor, "company_profile",  "user_id", "INTEGER")
    _safe_add_column(cursor, "email_templates",  "user_id", "INTEGER")
    _safe_add_column(cursor, "gmail_config",     "user_id", "INTEGER")
    _safe_add_column(cursor, "email_campaigns",  "user_id", "INTEGER")
    _safe_add_column(cursor, "agent_runs",       "user_id", "INTEGER")

    # ── Users table ─────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email        TEXT DEFAULT '',
            full_name    TEXT DEFAULT '',
            role         TEXT DEFAULT 'user',
            is_active    INTEGER DEFAULT 1,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    _seed_country_sources(conn)
    _seed_search_providers(conn)
    _seed_admin_user(conn)
    _migrate_to_user_scoped(conn)
    conn.close()


def _safe_add_column(cursor, table: str, column: str, definition: str):
    """Add a column only if it doesn't already exist — safe for existing DBs."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except Exception:
        pass  # column already exists — ignore


def _migrate_to_user_scoped(conn):
    """Assign existing data (user_id IS NULL) to the admin user so nothing is lost."""
    row = conn.execute("SELECT id FROM users WHERE username='admin' LIMIT 1").fetchone()
    if not row:
        return
    admin_id = row["id"]
    for table in ("company_profile", "email_templates", "gmail_config", "email_campaigns", "agent_runs"):
        conn.execute(
            f"UPDATE {table} SET user_id=? WHERE user_id IS NULL",
            (admin_id,),
        )
    conn.commit()


# ── Country Sources Seed Data ─────────────────────────────────────────────────

_SEED_SOURCES = [
    # UAE
    ("UAE", "Both", "https://www.yellowpages.ae/search/"),
    ("UAE", "Both", "https://www.easyuae.com/en/dubai/"),
    ("UAE", "Both", "https://emaratfinder.com/categories/en/"),
    ("UAE", "B2B",  "https://ae.kompass.com/"),
    ("UAE", "B2B",  "https://www.dubaiexporters.com/"),
    ("UAE", "B2B",  "https://www.gulfjobseeker.com/employer/"),
    ("UAE", "B2B",  "https://www.uaeexporters.net/"),
    ("UAE", "B2B",  "https://www.b2bsuppliers.ae/"),
    ("UAE", "B2B",  "https://www.tradeareabia.com/"),
    ("UAE", "B2C",  "https://www.dubizzle.com/"),
    ("UAE", "B2C",  "https://www.opensooq.com/en"),
    # India
    ("India", "Both", "https://www.justdial.com/"),
    ("India", "Both", "https://www.sulekha.com/"),
    ("India", "B2B",  "https://www.indiamart.com/"),
    ("India", "B2B",  "https://www.tradeindia.com/"),
    ("India", "B2B",  "https://www.exportersindia.com/"),
    ("India", "B2B",  "https://www.yellowpages.co.in/"),
    ("India", "B2C",  "https://www.urbanclap.com/"),
    # Saudi Arabia
    ("Saudi Arabia", "Both", "https://www.yellowpages.com.sa/"),
    ("Saudi Arabia", "B2B",  "https://sa.kompass.com/"),
    ("Saudi Arabia", "B2B",  "https://www.saudibusiness.com/"),
    ("Saudi Arabia", "B2B",  "https://www.saudiexporter.com/"),
    ("Saudi Arabia", "B2C",  "https://www.opensooq.com/en"),
    ("Saudi Arabia", "B2C",  "https://haraj.com.sa/"),
    # USA
    ("USA", "Both", "https://www.yellowpages.com/"),
    ("USA", "Both", "https://www.manta.com/"),
    ("USA", "B2B",  "https://www.thomasnet.com/"),
    ("USA", "B2B",  "https://clutch.co/"),
    ("USA", "B2B",  "https://www.kompass.com/a/usa/"),
    ("USA", "B2C",  "https://www.yelp.com/"),
    ("USA", "B2C",  "https://www.angi.com/"),
    # UK
    ("UK", "Both", "https://www.yell.com/"),
    ("UK", "B2B",  "https://www.kompass.com/a/united-kingdom/"),
    ("UK", "B2B",  "https://www.companieshouse.gov.uk/"),
    ("UK", "B2C",  "https://www.checkatrade.com/"),
    # Australia
    ("Australia", "Both", "https://www.yellowpages.com.au/"),
    ("Australia", "B2B",  "https://www.kompass.com/a/australia/"),
    ("Australia", "B2C",  "https://www.hipages.com.au/"),
    # Qatar
    ("Qatar", "Both", "https://www.yellowpages.com.qa/"),
    ("Qatar", "B2B",  "https://qa.kompass.com/"),
    ("Qatar", "B2B",  "https://www.qatarbusinessdirectory.com/"),
    ("Qatar", "B2C",  "https://www.opensooq.com/en"),
    # Kuwait
    ("Kuwait", "Both", "https://www.yellowpages.com.kw/"),
    ("Kuwait", "B2B",  "https://kw.kompass.com/"),
    ("Kuwait", "B2C",  "https://www.opensooq.com/en"),
    # Bahrain
    ("Bahrain", "Both", "https://www.yellowpages.com.bh/"),
    ("Bahrain", "B2B",  "https://bh.kompass.com/"),
    ("Bahrain", "B2C",  "https://www.opensooq.com/en"),
    # Oman
    ("Oman", "Both", "https://www.yellowpages.com.om/"),
    ("Oman", "B2B",  "https://om.kompass.com/"),
    ("Oman", "B2C",  "https://www.opensooq.com/en"),
    # Singapore
    ("Singapore", "Both", "https://www.yellowpages.com.sg/"),
    ("Singapore", "B2B",  "https://sg.kompass.com/"),
    ("Singapore", "B2B",  "https://www.sgpbusiness.com/"),
    ("Singapore", "B2C",  "https://www.carousell.sg/"),
    # Germany
    ("Germany", "Both", "https://www.gelbeseiten.de/"),
    ("Germany", "B2B",  "https://de.kompass.com/"),
    ("Germany", "B2B",  "https://www.wlw.de/"),
    ("Germany", "B2C",  "https://www.yelp.de/"),
    # Canada
    ("Canada", "Both", "https://www.yellowpages.ca/"),
    ("Canada", "B2B",  "https://ca.kompass.com/"),
    ("Canada", "B2C",  "https://www.kijiji.ca/"),
]


def _seed_country_sources(conn):
    """Insert seed data only for rows that don't already exist (IGNORE conflict)."""
    conn.executemany(
        "INSERT OR IGNORE INTO country_sources (country, business_type, url) VALUES (?, ?, ?)",
        _SEED_SOURCES,
    )
    conn.commit()


# ── Country Sources CRUD ──────────────────────────────────────────────────────

def get_all_countries() -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT country FROM country_sources ORDER BY country ASC"
    ).fetchall()
    conn.close()
    return [r["country"] for r in rows]


def get_sources_for_country(country: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM country_sources WHERE country=? ORDER BY business_type, url",
        (country,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_directory_urls(country: str, business_type: str) -> list[str]:
    """
    Return active URLs for a country matching the requested business_type.
    'Both' rows always included. B2B rows only if biz_type is B2B or Both. Same for B2C.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT url FROM country_sources
           WHERE country=? AND is_active=1
             AND (business_type='Both'
                  OR business_type=?
                  OR ?='Both')
           ORDER BY business_type, url""",
        (country, business_type, business_type),
    ).fetchall()
    conn.close()
    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            result.append(r["url"])
    return result


def add_country_source(country: str, business_type: str, url: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO country_sources (country, business_type, url) VALUES (?, ?, ?)",
            (country.strip(), business_type, url.strip()),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def toggle_country_source(source_id: int, is_active: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE country_sources SET is_active=? WHERE id=?",
        (1 if is_active else 0, source_id),
    )
    conn.commit()
    conn.close()


def update_country_source(source_id: int, country: str, business_type: str, url: str):
    conn = get_connection()
    conn.execute(
        "UPDATE country_sources SET country=?, business_type=?, url=? WHERE id=?",
        (country.strip(), business_type, url.strip(), source_id),
    )
    conn.commit()
    conn.close()


def get_all_country_sources() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM country_sources ORDER BY country ASC, business_type ASC, url ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_country_source(source_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM country_sources WHERE id=?", (source_id,))
    conn.commit()
    conn.close()


# ── Search Providers Seed + CRUD ─────────────────────────────────────────────

_SEED_PROVIDERS = [
    # name, display_name, type, enabled, api_key, description
    (
        "duckduckgo", "DuckDuckGo", "free", 1, "",
        "Free search engine. No API key needed. Good for general queries.",
    ),
    (
        "bing_scrape", "Bing (Free Scraping)", "free", 0, "",
        "Scrapes Bing.com via Playwright. Disabled by default — Bing detects headless browsers. Enable if you have a rotating proxy.",
    ),
    (
        "google_maps", "Google Maps / Business", "free", 1, "",
        "Scrapes Google Maps search results. Gets business name, phone, website and address directly.",
    ),
    (
        "brave", "Brave Search API", "paid", 0, "",
        "2000 free queries/month then paid. Add API key from brave.com/search/api to enable.",
    ),
    (
        "serper", "Serper.dev (Google Search)", "paid", 0, "",
        "2500 free Google queries then paid. Add API key from serper.dev to enable.",
    ),
    (
        "serpapi", "SerpAPI (Google Search)", "paid", 0, "",
        "100 free Google searches/month then paid. Add API key from serpapi.com to enable.",
    ),
]


def _seed_search_providers(conn):
    conn.executemany(
        """INSERT OR IGNORE INTO search_providers
               (name, display_name, provider_type, is_enabled, api_key, description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        _SEED_PROVIDERS,
    )
    conn.commit()


def get_all_search_providers() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM search_providers ORDER BY provider_type ASC, id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_enabled_search_providers() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM search_providers WHERE is_enabled=1 ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_search_provider(provider_id: int, is_enabled: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE search_providers SET is_enabled=? WHERE id=?",
        (1 if is_enabled else 0, provider_id),
    )
    conn.commit()
    conn.close()


def save_provider_api_key(provider_id: int, api_key: str):
    conn = get_connection()
    conn.execute(
        "UPDATE search_providers SET api_key=?, is_enabled=1 WHERE id=?",
        (api_key.strip(), provider_id),
    )
    conn.commit()
    conn.close()


def clear_provider_api_key(provider_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE search_providers SET api_key='', is_enabled=0 WHERE id=?",
        (provider_id,),
    )
    conn.commit()
    conn.close()


# ── Company Profile ──────────────────────────────────────────────────────────

def save_company_profile(data: dict, user_id: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM company_profile WHERE user_id=?", (user_id,))
    cursor.execute(
        """INSERT INTO company_profile (company_name, industry, website, description, user_id)
           VALUES (:company_name, :industry, :website, :description, :user_id)""",
        {**data, "user_id": user_id},
    )
    conn.commit()
    conn.close()


def get_company_profile(user_id: int = 0) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM company_profile WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Products ─────────────────────────────────────────────────────────────────

def save_product(company_profile_id: int, product_name: str, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (company_profile_id, product_name, description) VALUES (?, ?, ?)",
        (company_profile_id, product_name.strip(), description.strip()),
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id


def get_products(company_profile_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE company_profile_id=? ORDER BY id ASC",
        (company_profile_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_product(product_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM target_audience WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM leads WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def get_product_by_id(product_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Target Audience ──────────────────────────────────────────────────────────

def get_all_target_audiences(product_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM target_audience WHERE product_id=? ORDER BY id ASC",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_target_audience(product_id: int) -> dict | None:
    """Legacy — returns first row for backward compat with pipeline."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM target_audience WHERE product_id=? ORDER BY id ASC LIMIT 1",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_target_audience(product_id: int, data: dict):
    conn = get_connection()
    conn.execute(
        """INSERT INTO target_audience
               (product_id, industry, location, country, business_type, roles, company_size, keywords, competitors)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            product_id,
            data.get("industry", ""),
            data.get("location", ""),
            data.get("country", ""),
            data.get("business_type", "B2B"),
            data.get("roles", ""),
            data.get("company_size", ""),
            data.get("keywords", ""),
            data.get("competitors", ""),
        ),
    )
    conn.commit()
    conn.close()


def update_target_audience(ta_id: int, data: dict):
    conn = get_connection()
    conn.execute(
        """UPDATE target_audience SET industry=?, location=?, country=?, business_type=?,
               roles=?, company_size=?, keywords=?, competitors=? WHERE id=?""",
        (
            data.get("industry", ""),
            data.get("location", ""),
            data.get("country", ""),
            data.get("business_type", "B2B"),
            data.get("roles", ""),
            data.get("company_size", ""),
            data.get("keywords", ""),
            data.get("competitors", ""),
            ta_id,
        ),
    )
    conn.commit()
    conn.close()


def delete_target_audience(ta_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM target_audience WHERE id=?", (ta_id,))
    conn.commit()
    conn.close()


def save_target_audience(product_id: int, data: dict):
    """Legacy — kept for pipeline compatibility. Upserts single row."""
    existing = get_target_audience(product_id)
    if existing:
        update_target_audience(existing["id"], data)
    else:
        add_target_audience(product_id, data)


# ── Leads ────────────────────────────────────────────────────────────────────

def lead_email_exists(product_id: int, email: str) -> bool:
    """Return True if a lead with this email already exists for the product."""
    if not email:
        return False
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM leads WHERE product_id=? AND email=? LIMIT 1",
        (product_id, email.lower().strip()),
    ).fetchone()
    conn.close()
    return row is not None


def save_leads(leads: list[dict], product_id: int, run_id: int = None):
    if not leads:
        return
    conn = get_connection()
    cursor = conn.cursor()
    for lead in leads:
        cursor.execute(
            """INSERT INTO leads
               (product_id, run_id, name, company, role, email, phone, linkedin,
                industry, location, source, score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                product_id,
                run_id,
                lead.get("name", ""),
                lead.get("company", ""),
                lead.get("role", ""),
                lead.get("email", ""),
                lead.get("phone", ""),
                lead.get("linkedin", ""),
                lead.get("industry", ""),
                lead.get("location", ""),
                lead.get("source", ""),
                lead.get("score", 0),
            ),
        )
    conn.commit()
    conn.close()


def update_lead_stage(lead_id: int, stage: str):
    conn = get_connection()
    conn.execute("UPDATE leads SET stage=? WHERE id=?", (stage, lead_id))
    conn.commit()
    conn.close()


def update_lead_notes(lead_id: int, notes: str):
    conn = get_connection()
    conn.execute("UPDATE leads SET notes=? WHERE id=?", (notes, lead_id))
    conn.commit()
    conn.close()


def get_campaign_analytics(campaign_id: int) -> dict:
    """Return sent/replied/failed counts and reply rate for a campaign."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM email_sends WHERE campaign_id=? GROUP BY status",
        (campaign_id,),
    ).fetchall()
    conn.close()
    stats = {r["status"]: r["cnt"] for r in rows}
    sent     = stats.get("sent", 0)
    replied  = stats.get("replied", 0)
    auto_rep = stats.get("auto_reply", 0)
    failed   = stats.get("failed", 0)
    total    = sent + replied + auto_rep + failed
    reply_rate = round(replied / total * 100, 1) if total > 0 else 0.0
    return {
        "total": total, "sent": sent, "replied": replied,
        "auto_reply": auto_rep, "failed": failed, "reply_rate": reply_rate,
    }


def get_all_leads(product_id: int = None, user_id: int = 0) -> list[dict]:
    conn = get_connection()
    if product_id:
        rows = conn.execute(
            "SELECT * FROM leads WHERE product_id=? ORDER BY created_at DESC", (product_id,)
        ).fetchall()
    elif user_id:
        rows = conn.execute(
            """SELECT l.* FROM leads l
               JOIN products p ON l.product_id = p.id
               JOIN company_profile cp ON p.company_profile_id = cp.id
               WHERE cp.user_id = ?
               ORDER BY l.created_at DESC""",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_leads(product_id: int = None):
    conn = get_connection()
    if product_id:
        conn.execute("DELETE FROM leads WHERE product_id=?", (product_id,))
    else:
        conn.execute("DELETE FROM leads")
    conn.commit()
    conn.close()


# ── Agent Runs ───────────────────────────────────────────────────────────────

def create_agent_run(product_id: int, mode: str = "start", user_id: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agent_runs (product_id, run_time, mode, status, leads_found, notes, user_id) VALUES (?, ?, ?, 'running', 0, '', ?)",
        (product_id, datetime.now().isoformat(), mode, user_id),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def update_agent_run(run_id: int, status: str, leads_found: int, notes: str = ""):
    conn = get_connection()
    conn.execute(
        "UPDATE agent_runs SET status=?, leads_found=?, notes=? WHERE id=?",
        (status, leads_found, notes, run_id),
    )
    conn.commit()
    conn.close()


def get_agent_runs(product_id: int = None, user_id: int = 0) -> list[dict]:
    conn = get_connection()
    if product_id and user_id:
        rows = conn.execute(
            "SELECT * FROM agent_runs WHERE product_id=? AND user_id=? ORDER BY id DESC",
            (product_id, user_id),
        ).fetchall()
    elif product_id:
        rows = conn.execute(
            "SELECT * FROM agent_runs WHERE product_id=? ORDER BY id DESC", (product_id,)
        ).fetchall()
    elif user_id:
        rows = conn.execute(
            "SELECT * FROM agent_runs WHERE user_id=? ORDER BY id DESC", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM agent_runs ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Agent Logs ───────────────────────────────────────────────────────────────

def log_agent_step(run_id: int, agent_name: str, message: str, level: str = "INFO"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO agent_logs (run_id, agent_name, message, level, created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, agent_name, message, level, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_logs_for_run(run_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_logs WHERE run_id=? ORDER BY id ASC", (run_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_logs(limit: int = 200) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_agent_run(run_id: int):
    """Delete a pipeline run and everything related: logs, email sends, leads, run record."""
    conn = get_connection()
    # Delete email_sends for leads belonging to this run (must come before leads delete)
    conn.execute(
        "DELETE FROM email_sends WHERE lead_id IN (SELECT id FROM leads WHERE run_id=?)",
        (run_id,),
    )
    conn.execute("DELETE FROM agent_logs WHERE run_id=?", (run_id,))
    conn.execute("DELETE FROM leads WHERE run_id=?", (run_id,))
    conn.execute("DELETE FROM agent_runs WHERE id=?", (run_id,))
    conn.commit()
    conn.close()


def clear_agent_logs():
    """Delete all agent_logs rows (keeps runs and leads intact)."""
    conn = get_connection()
    conn.execute("DELETE FROM agent_logs")
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — EMAIL CAMPAIGN DB HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# ── Gmail Config ──────────────────────────────────────────────────────────────

def save_gmail_config(email: str, app_password: str, user_id: int = 0):
    conn = get_connection()
    conn.execute("DELETE FROM gmail_config WHERE user_id=?", (user_id,))
    conn.execute(
        "INSERT INTO gmail_config (email, app_password, user_id) VALUES (?, ?, ?)",
        (email, app_password, user_id),
    )
    conn.commit()
    conn.close()


def get_gmail_config(user_id: int = 0) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM gmail_config WHERE user_id=? LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Email Templates ───────────────────────────────────────────────────────────

def save_email_template(name: str, subject: str, body: str, template_id: int = None, user_id: int = 0) -> int:
    conn = get_connection()
    if template_id:
        conn.execute(
            "UPDATE email_templates SET name=?, subject=?, body=? WHERE id=?",
            (name, subject, body, template_id),
        )
        conn.commit()
        conn.close()
        return template_id
    else:
        cur = conn.execute(
            "INSERT INTO email_templates (name, subject, body, user_id) VALUES (?, ?, ?, ?)",
            (name, subject, body, user_id),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id


def get_email_templates(user_id: int = 0) -> list[dict]:
    conn = get_connection()
    if user_id:
        rows = conn.execute(
            "SELECT * FROM email_templates WHERE user_id=? ORDER BY id DESC", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM email_templates ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_email_template_by_id(template_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM email_templates WHERE id=?", (template_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_email_template(template_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM email_templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()


# ── Email Campaigns ───────────────────────────────────────────────────────────

def create_email_campaign(name: str, template_id: int, product_id: int = None, user_id: int = 0) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO email_campaigns (name, template_id, product_id, status, user_id) VALUES (?, ?, ?, 'draft', ?)",
        (name, template_id, product_id, user_id),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_email_campaigns(user_id: int = 0) -> list[dict]:
    conn = get_connection()
    if user_id:
        rows = conn.execute("""
            SELECT c.*, t.name as template_name
            FROM email_campaigns c
            LEFT JOIN email_templates t ON c.template_id = t.id
            WHERE c.user_id = ?
            ORDER BY c.id DESC
        """, (user_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT c.*, t.name as template_name
            FROM email_campaigns c
            LEFT JOIN email_templates t ON c.template_id = t.id
            ORDER BY c.id DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_email_campaign(campaign_id: int):
    """Delete a campaign and all its send records."""
    conn = get_connection()
    conn.execute("DELETE FROM email_sends WHERE campaign_id=?", (campaign_id,))
    conn.execute("DELETE FROM email_campaigns WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()


def update_email_campaign_name(campaign_id: int, name: str):
    conn = get_connection()
    conn.execute("UPDATE email_campaigns SET name=? WHERE id=?", (name.strip(), campaign_id))
    conn.commit()
    conn.close()


def update_campaign_status(campaign_id: int, status: str, sent_count: int = None):
    conn = get_connection()
    if sent_count is not None:
        conn.execute(
            "UPDATE email_campaigns SET status=?, sent_count=? WHERE id=?",
            (status, sent_count, campaign_id),
        )
    else:
        conn.execute("UPDATE email_campaigns SET status=? WHERE id=?", (status, campaign_id))
    conn.commit()
    conn.close()


# ── Email Sends ───────────────────────────────────────────────────────────────

def log_email_send(campaign_id: int, lead_id: int, email_to: str,
                   subject: str, status: str = "sent", message_id: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO email_sends
               (campaign_id, lead_id, email_to, subject, status, message_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (campaign_id, lead_id, email_to, subject, status, message_id),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_sends_for_campaign(campaign_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, l.name as lead_name, l.company as lead_company
        FROM email_sends s
        LEFT JOIN leads l ON s.lead_id = l.id
        WHERE s.campaign_id = ?
        ORDER BY s.id DESC
    """, (campaign_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_lead_replied(lead_id: int, is_auto: bool = False):
    status = "auto_reply" if is_auto else "replied"
    now    = datetime.utcnow().isoformat()
    conn   = get_connection()
    conn.execute(
        "UPDATE leads SET email_status=?, email_replied_at=? WHERE id=?",
        (status, now, lead_id),
    )
    conn.commit()
    conn.close()


def mark_lead_emailed(lead_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE leads SET email_status='sent', email_sent_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), lead_id),
    )
    conn.commit()
    conn.close()


def get_leads_for_campaign(product_id: int = None, user_id: int = 0, only_with_email: bool = True) -> list[dict]:
    """Return leads eligible for emailing — filtered by product or user."""
    conn = get_connection()
    if user_id and not product_id:
        query = """SELECT l.* FROM leads l
                   JOIN products p ON l.product_id = p.id
                   JOIN company_profile cp ON p.company_profile_id = cp.id
                   WHERE cp.user_id = ?"""
        params: list = [user_id]
        if only_with_email:
            query += " AND l.email != '' AND l.email IS NOT NULL"
        query += " ORDER BY l.id DESC"
    else:
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        if only_with_email:
            query += " AND email != '' AND email IS NOT NULL"
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sends(user_id: int = 0) -> list[dict]:
    conn = get_connection()
    if user_id:
        rows = conn.execute("""
            SELECT s.*, l.name as lead_name, l.company, c.name as campaign_name
            FROM email_sends s
            LEFT JOIN leads l ON s.lead_id = l.id
            LEFT JOIN email_campaigns c ON s.campaign_id = c.id
            WHERE c.user_id = ?
            ORDER BY s.id DESC
        """, (user_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT s.*, l.name as lead_name, l.company, c.name as campaign_name
            FROM email_sends s
            LEFT JOIN leads l ON s.lead_id = l.id
            LEFT JOIN email_campaigns c ON s.campaign_id = c.id
            ORDER BY s.id DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_send_replied(message_id: str, is_auto: bool = False):
    """Mark a specific sent email as replied using its Message-ID."""
    status = "auto_reply" if is_auto else "replied"
    now    = datetime.utcnow().isoformat()
    conn   = get_connection()
    row = conn.execute(
        "SELECT * FROM email_sends WHERE message_id=?", (message_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE email_sends SET status=?, replied_at=? WHERE message_id=?",
            (status, now, message_id),
        )
        conn.commit()
        mark_lead_replied(row["lead_id"], is_auto=is_auto)
    conn.close()


def update_send_replied_by_email(to_email: str, is_auto: bool = False):
    """
    Fallback: mark most recent sent email to `to_email` as replied.
    Used when Message-ID was not recorded (older sends).
    Only updates rows with status='sent' to avoid overwriting already-marked rows.
    """
    status = "auto_reply" if is_auto else "replied"
    now    = datetime.utcnow().isoformat()
    conn   = get_connection()
    row = conn.execute(
        "SELECT * FROM email_sends WHERE email_to=? AND status='sent' ORDER BY id DESC LIMIT 1",
        (to_email,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE email_sends SET status=?, replied_at=? WHERE id=?",
            (status, now, row["id"]),
        )
        conn.commit()
        mark_lead_replied(row["lead_id"], is_auto=is_auto)
    conn.close()


# ── User Authentication ───────────────────────────────────────────────────────
import hashlib, os as _os


def _hash_password(password: str) -> str:
    salt = _os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return test == h
    except Exception:
        return False


def _seed_admin_user(conn):
    """Create the default admin user if no users exist yet."""
    row = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
    if not row:
        pwd_hash = _hash_password("admin")
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, email, full_name, role) VALUES (?,?,?,?,?)",
            ("admin", pwd_hash, "admin@leadforge.ai", "Administrator", "admin"),
        )
        conn.commit()


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict | None:
    """Return user dict if credentials are valid, else None."""
    user = get_user_by_username(username)
    if user and _verify_password(password, user["password_hash"]):
        return user
    return None


def register_user(username: str, password: str, email: str = "", full_name: str = "") -> tuple[bool, str]:
    """Create a new user. Returns (success, error_message)."""
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if get_user_by_username(username):
        return False, "Username already taken."
    pwd_hash = _hash_password(password)
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (username, password_hash, email, full_name, role) VALUES (?,?,?,?,?)",
            (username.strip(), pwd_hash, email.strip(), full_name.strip(), "user"),
        )
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def get_all_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, email, full_name, role, is_active, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_user_role(user_id: int, role: str):
    conn = get_connection()
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()
    conn.close()


def deactivate_user(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

