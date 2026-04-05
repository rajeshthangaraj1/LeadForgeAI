import re
import hashlib
from typing import Any


def clean_email(email: str) -> str:
    if not email:
        return ""
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return email if re.match(pattern, email) else ""


def clean_phone(phone: str) -> str:
    if not phone:
        return ""
    phone = phone.strip()
    # Keep only digits, +, -, spaces, parentheses
    cleaned = re.sub(r"[^\d\+\-\s\(\)]", "", phone).strip()
    # Must have at least 7 digits
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 7:
        return ""
    return cleaned


def clean_linkedin(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if "linkedin.com" not in url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    return url


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    suffixes = [
        " inc", " inc.", " llc", " llc.", " ltd", " ltd.", " co.", " co",
        " corp", " corp.", " limited", " pvt", " pvt.",
    ]
    name = name.strip()
    lower = name.lower()
    for s in suffixes:
        if lower.endswith(s):
            name = name[: len(name) - len(s)].strip()
            break
    return name.title()


def lead_fingerprint(lead: dict) -> str:
    key = f"{lead.get('email','').lower()}|{lead.get('name','').lower()}|{lead.get('company','').lower()}"
    return hashlib.md5(key.encode()).hexdigest()


def deduplicate_leads(leads: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for lead in leads:
        fp = lead_fingerprint(lead)
        if fp not in seen:
            seen.add(fp)
            unique.append(lead)
    return unique


def chunk_list(lst: list[Any], size: int) -> list[list[Any]]:
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def truncate_text(text: str, max_chars: int = 4000) -> str:
    return text[:max_chars] if len(text) > max_chars else text
