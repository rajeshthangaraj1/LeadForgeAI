"""
Email Utilities — Phase 2
Gmail SMTP (send) + IMAP (reply monitoring)
Uses App Password — no OAuth needed.
"""
import smtplib
import imaplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import make_msgid
from datetime import datetime, timedelta


# ── Auto-reply detection ───────────────────────────────────────────────────────

_AUTO_REPLY_SUBJECTS = [
    "out of office", "auto:", "automatic reply", "autoreply",
    "auto-reply", "away from", "on vacation", "on leave",
    "i am out", "i'm out", "will be back", "currently away",
    "office closed", "public holiday", "annual leave",
]

_AUTO_REPLY_HEADERS = [
    "auto-submitted", "x-autoreply", "x-autorespond",
    "x-autoresponder", "x-auto-response-suppress",
]


def is_auto_reply(msg) -> bool:
    """Return True if the email looks like an auto-reply / out-of-office."""
    # Check headers
    for h in _AUTO_REPLY_HEADERS:
        val = msg.get(h, "").lower()
        if val and val not in ("no", "none", ""):
            return True
    if msg.get("Precedence", "").lower() in ("auto-reply", "bulk", "junk"):
        return True

    # Check subject
    subj = _decode_header_str(msg.get("Subject", "")).lower()
    if any(kw in subj for kw in _AUTO_REPLY_SUBJECTS):
        return True

    return False


def _decode_header_str(value: str) -> str:
    try:
        parts = decode_header(value)
        decoded = ""
        for part, enc in parts:
            if isinstance(part, bytes):
                decoded += part.decode(enc or "utf-8", errors="ignore")
            else:
                decoded += str(part)
        return decoded
    except Exception:
        return value or ""


# ── SMTP — Send email ─────────────────────────────────────────────────────────

def send_email(
    gmail_email: str,
    app_password: str,
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> tuple[bool, str, str]:
    """
    Send one email via Gmail SMTP.
    Returns (success: bool, message_id: str, error: str)
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = gmail_email
        msg["To"]      = to_email
        msg["Subject"] = subject

        # Explicitly generate Message-ID so replies can be matched later
        domain = gmail_email.split("@")[-1] if "@" in gmail_email else "gmail.com"
        message_id = make_msgid(domain=domain)
        msg["Message-ID"] = message_id

        # Plain text + HTML versions
        plain = body
        html  = body.replace("\n", "<br>")
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(f"<html><body>{html}</body></html>", "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(gmail_email, app_password)
            server.sendmail(gmail_email, to_email, msg.as_string())

        return True, message_id, ""

    except smtplib.SMTPAuthenticationError:
        return False, "", "Authentication failed — check your Gmail App Password."
    except smtplib.SMTPRecipientsRefused:
        return False, "", f"Recipient refused: {to_email}"
    except Exception as e:
        return False, "", str(e)


def test_smtp_connection(gmail_email: str, app_password: str,
                          smtp_host: str = "smtp.gmail.com",
                          smtp_port: int = 587) -> tuple[bool, str]:
    """Quick SMTP login test without sending. Returns (ok, error_message)."""
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(gmail_email, app_password)
        return True, ""
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed — wrong email or App Password."
    except Exception as e:
        return False, str(e)


# ── Template rendering ────────────────────────────────────────────────────────

def render_template(subject: str, body: str, lead: dict) -> tuple[str, str]:
    """
    Replace placeholders in subject + body with lead data.
    Supported: {name} {first_name} {company} {role} {industry} {location} {email}
    """
    first_name = (lead.get("name", "") or "").split()[0] if lead.get("name") else "there"
    replacements = {
        "{name}":      lead.get("name", "")      or "there",
        "{first_name}": first_name,
        "{company}":   lead.get("company", "")   or "your company",
        "{role}":      lead.get("role", "")       or "your role",
        "{industry}":  lead.get("industry", "")   or "your industry",
        "{location}":  lead.get("location", "")   or "",
        "{email}":     lead.get("email", "")      or "",
    }
    rendered_subject = subject
    rendered_body    = body
    for placeholder, value in replacements.items():
        rendered_subject = rendered_subject.replace(placeholder, value)
        rendered_body    = rendered_body.replace(placeholder, value)
    return rendered_subject, rendered_body


# ── IMAP — Check for replies ──────────────────────────────────────────────────

def fetch_replies(
    gmail_email: str,
    app_password: str,
    sent_message_ids: list[str],
    days_back: int = 30,
    imap_host: str = "imap.gmail.com",
    imap_port: int = 993,
    sent_to_emails: list[str] = None,
) -> list[dict]:
    """
    Connect to Gmail via IMAP and find replies to our sent emails.

    Primary match: In-Reply-To / References header contains one of our Message-IDs.
    Fallback match: inbox email is FROM an address in sent_to_emails (covers older
    sends where Message-ID was not stored).

    Returns list of dicts:
      { message_id, in_reply_to, subject, sender, sender_email,
        received_at, is_auto_reply, matched_by }
      matched_by = "message_id" | "sender_email"
    """
    results = []
    valid_ids    = {mid for mid in (sent_message_ids or []) if mid}
    fallback_set = {e.lower().strip() for e in (sent_to_emails or []) if e}

    if not valid_ids and not fallback_set:
        return results

    try:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(gmail_email, app_password)
        mail.select("INBOX")

        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        _, data = mail.search(None, f'(SINCE "{since_date}")')

        # Track Message-IDs we already returned to avoid duplicates
        seen_incoming: set[str] = set()

        for num in data[0].split():
            try:
                _, msg_data = mail.fetch(num, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                incoming_id = msg.get("Message-ID", "").strip()
                if incoming_id and incoming_id in seen_incoming:
                    continue

                in_reply_to = msg.get("In-Reply-To", "").strip()
                references  = msg.get("References", "").strip()
                raw_from    = msg.get("From", "")

                # Extract bare email address from "Name <addr@x>" or "addr@x"
                m = re.search(r"<([^>]+)>", raw_from)
                sender_email = (m.group(1) if m else raw_from).lower().strip()

                # Primary: match by Message-ID
                matched_id  = None
                matched_by  = None
                for sent_id in valid_ids:
                    if sent_id in in_reply_to or sent_id in references:
                        matched_id = sent_id
                        matched_by = "message_id"
                        break

                # Fallback: match by sender address
                if not matched_id and sender_email in fallback_set:
                    matched_id = sender_email   # used as key by caller
                    matched_by = "sender_email"

                if matched_id:
                    if incoming_id:
                        seen_incoming.add(incoming_id)
                    results.append({
                        "message_id":    incoming_id,
                        "in_reply_to":   matched_id,
                        "subject":       _decode_header_str(msg.get("Subject", "")),
                        "sender":        raw_from,
                        "sender_email":  sender_email,
                        "received_at":   msg.get("Date", ""),
                        "is_auto_reply": is_auto_reply(msg),
                        "matched_by":    matched_by,
                    })
            except Exception:
                continue

        mail.logout()

    except imaplib.IMAP4.error as e:
        raise RuntimeError(f"IMAP error: {e}")
    except Exception as e:
        raise RuntimeError(f"Reply check failed: {e}")

    return results
