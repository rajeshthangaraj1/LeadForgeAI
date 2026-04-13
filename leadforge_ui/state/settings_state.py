import reflex as rx
import sys, os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leadforge_ui.state.auth import AuthState
from database.sqlite_db import (
    get_gmail_config,
    save_gmail_config,
    get_all_search_providers,
    toggle_search_provider,
    save_provider_api_key,
    clear_provider_api_key,
)
from utils.email_utils import test_smtp_connection
import config.settings as cfg


class ProviderDict(TypedDict):
    id: int
    name: str
    display_name: str
    provider_type: str
    is_enabled: int
    api_key: str
    description: str


class SettingsState(AuthState):
    """Settings page — Gmail, Search Providers, Model config."""

    # ── Gmail ──────────────────────────────────────────────────────────────────
    gmail_email: str = ""
    gmail_password: str = ""
    gmail_smtp_host: str = "smtp.gmail.com"
    gmail_smtp_port: str = "587"
    gmail_imap_host: str = "imap.gmail.com"
    gmail_imap_port: str = "993"
    gmail_test_result: str = ""
    gmail_test_ok: bool = False

    # ── Search providers ───────────────────────────────────────────────────────
    providers: list[ProviderDict] = []
    provider_api_keys: dict[str, str] = {}

    # ── Model ──────────────────────────────────────────────────────────────────
    model_name: str = ""
    ollama_url: str = ""

    # ── Load ───────────────────────────────────────────────────────────────────

    def load_settings(self):
        # Gmail
        gc = get_gmail_config(self.user_id)
        if gc:
            self.gmail_email = gc.get("email") or ""
            self.gmail_password = gc.get("app_password") or ""
            self.gmail_smtp_host = gc.get("smtp_host") or "smtp.gmail.com"
            self.gmail_smtp_port = str(gc.get("smtp_port") or 587)
            self.gmail_imap_host = gc.get("imap_host") or "imap.gmail.com"
            self.gmail_imap_port = str(gc.get("imap_port") or 993)
        # Providers — normalize to ProviderDict
        raw = get_all_search_providers()
        self.providers = [
            {
                "id": int(p.get("id") or 0),
                "name": str(p.get("name") or ""),
                "display_name": str(p.get("display_name") or ""),
                "provider_type": str(p.get("provider_type") or "free"),
                "is_enabled": int(p.get("is_enabled") or 0),
                "api_key": str(p.get("api_key") or ""),
                "description": str(p.get("description") or ""),
            }
            for p in raw
        ]
        # Model
        self.model_name = cfg.OLLAMA_MODEL
        self.ollama_url = cfg.OLLAMA_BASE_URL

    # ── Gmail ──────────────────────────────────────────────────────────────────

    def save_gmail(self, form_data: dict):
        email = form_data.get("gmail_email", "").strip()
        pwd = form_data.get("gmail_password", "").strip()
        if not email or not pwd:
            return rx.toast.error("Email and App Password are required.")
        save_gmail_config(email, pwd, user_id=self.user_id)
        self.gmail_email = email
        self.gmail_password = pwd
        return rx.toast.success("Gmail settings saved.")

    def test_gmail(self):
        if not self.gmail_email or not self.gmail_password:
            return rx.toast.error("Save Gmail settings first.")
        ok, msg = test_smtp_connection(
            self.gmail_email, self.gmail_password,
            smtp_host=self.gmail_smtp_host,
            smtp_port=int(self.gmail_smtp_port),
        )
        self.gmail_test_ok = ok
        self.gmail_test_result = msg
        if ok:
            return rx.toast.success("SMTP connection successful!")
        return rx.toast.error(f"SMTP failed: {msg}")

    # ── Search providers ───────────────────────────────────────────────────────

    def toggle_provider(self, provider_id: int, enabled: bool):
        toggle_search_provider(provider_id, enabled)
        raw = get_all_search_providers()
        self.providers = [
            {
                "id": int(p.get("id") or 0),
                "name": str(p.get("name") or ""),
                "display_name": str(p.get("display_name") or ""),
                "provider_type": str(p.get("provider_type") or "free"),
                "is_enabled": int(p.get("is_enabled") or 0),
                "api_key": str(p.get("api_key") or ""),
                "description": str(p.get("description") or ""),
            }
            for p in raw
        ]

    def save_provider_key(self, provider_id: int, api_key: str):
        if api_key.strip():
            save_provider_api_key(provider_id, api_key.strip())
        else:
            clear_provider_api_key(provider_id)
        raw = get_all_search_providers()
        self.providers = [
            {
                "id": int(p.get("id") or 0),
                "name": str(p.get("name") or ""),
                "display_name": str(p.get("display_name") or ""),
                "provider_type": str(p.get("provider_type") or "free"),
                "is_enabled": int(p.get("is_enabled") or 0),
                "api_key": str(p.get("api_key") or ""),
                "description": str(p.get("description") or ""),
            }
            for p in raw
        ]
        return rx.toast.success("API key saved.")

    # ── Model ──────────────────────────────────────────────────────────────────

    def save_model_settings(self, form_data: dict):
        model = form_data.get("model_name", "").strip()
        url = form_data.get("ollama_url", "").strip()

        # Update in-memory config (agents read cfg.OLLAMA_MODEL at call time via module ref)
        if model:
            cfg.OLLAMA_MODEL = model
            self.model_name = model
        if url:
            cfg.OLLAMA_BASE_URL = url
            self.ollama_url = url

        # Persist to config/settings.py so changes survive restart
        settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "settings.py"
        )
        try:
            import re as _re
            with open(settings_path, "r") as f:
                text = f.read()
            if model:
                text = _re.sub(
                    r'(OLLAMA_MODEL\s*=\s*)["\'].*?["\']',
                    f'OLLAMA_MODEL    = "{cfg.OLLAMA_MODEL}"',
                    text,
                )
            if url:
                text = _re.sub(
                    r'(OLLAMA_BASE_URL\s*=\s*)["\'].*?["\']',
                    f'OLLAMA_BASE_URL = "{cfg.OLLAMA_BASE_URL}"',
                    text,
                )
            with open(settings_path, "w") as f:
                f.write(text)
        except Exception:
            pass  # In-memory update still worked; file write is best-effort

        return rx.toast.success(f"Model set to '{cfg.OLLAMA_MODEL}' — effective immediately.")
