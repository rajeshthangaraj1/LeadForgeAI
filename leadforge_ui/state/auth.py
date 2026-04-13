import reflex as rx
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.sqlite_db import authenticate_user, register_user, init_db


class AuthState(rx.State):
    """Handles user authentication — login, register, logout."""

    is_authenticated: bool = False
    username: str = ""
    full_name: str = ""
    user_role: str = ""
    user_id: int = 0
    login_error: str = ""
    register_error: str = ""
    register_success: str = ""

    # ── Login ──────────────────────────────────────────────────────────────────

    def login(self, form_data: dict):
        # Ensure DB + users table exist
        init_db()

        uname = (form_data.get("username") or "").strip()
        passwd = form_data.get("password") or ""

        user = authenticate_user(uname, passwd)
        if user:
            self.is_authenticated = True
            self.username = user["username"]
            self.full_name = user.get("full_name") or user["username"]
            self.user_role = user.get("role") or "user"
            self.user_id = int(user.get("id") or 0)
            self.login_error = ""
            return rx.redirect("/dashboard")
        else:
            self.login_error = "Invalid username or password."

    # ── Register ───────────────────────────────────────────────────────────────

    def register(self, form_data: dict):
        init_db()

        uname     = (form_data.get("username") or "").strip()
        passwd    = form_data.get("password") or ""
        confirm   = form_data.get("confirm_password") or ""
        email     = (form_data.get("email") or "").strip()
        full_name = (form_data.get("full_name") or "").strip()

        self.register_error = ""
        self.register_success = ""

        if passwd != confirm:
            self.register_error = "Passwords do not match."
            return

        ok, err = register_user(uname, passwd, email, full_name)
        if ok:
            self.register_success = f"Account created! You can now log in as '{uname}'."
            return rx.redirect("/login")
        else:
            self.register_error = err

    # ── Logout ─────────────────────────────────────────────────────────────────

    def logout(self):
        self.is_authenticated = False
        self.username = ""
        self.full_name = ""
        self.user_role = ""
        self.user_id = 0
        return rx.redirect("/login")

    # ── Auth guard — call in on_load of every protected page ──────────────────

    def check_auth(self):
        if not self.is_authenticated:
            return rx.redirect("/login")

    # ── Index redirect ─────────────────────────────────────────────────────────

    def redirect_from_index(self):
        if self.is_authenticated:
            return rx.redirect("/dashboard")
        return rx.redirect("/login")
