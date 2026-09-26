"""HR / careers email verification before sending."""

from __future__ import annotations

import re
from typing import Optional

ALLOWED_LOCALS = frozenset(
    {
        "careers",
        "jobs",
        "recruitment",
        "hr",
        "talent",
        "hiring",
        "recruiting",
        "recruiter",
        "people",
        "peopleops",
        "contact",
    }
)
WORK_EMAIL = re.compile(r"\b([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}(?:\.[a-z]{2,})?)\b", re.I)

CAREERS_EMAIL = re.compile(
    r"\b((?:careers|jobs|recruitment|hr|talent|hiring)@[a-z0-9.-]+\.[a-z]{2,}(?:\.[a-z]{2,})?)\b",
    re.I,
)


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def is_free_mail(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com"}


def extract_from_description(description: str) -> Optional[str]:
    if not description:
        return None
    for match in CAREERS_EMAIL.finditer(description):
        email = normalize_email(match.group(1))
        if not is_free_mail(email):
            return email
    return None


def normalize_obfuscated_email_text(text: str) -> str:
    """Collapse 'hr @ company . com' style obfuscation."""
    if not text:
        return ""
    t = text.replace("\u200b", "").replace("\ufeff", "")
    t = re.sub(r"\s*@\s*", "@", t)
    t = re.sub(r"\s*\[at\]\s*", "@", t, flags=re.I)
    t = re.sub(r"\s*\(at\)\s*", "@", t, flags=re.I)
    t = re.sub(r"\s+dot\s+", ".", t, flags=re.I)
    return t


def extract_work_emails(text: str) -> list[str]:
    """Corporate-style emails in post/JD text (no Gmail/Yahoo)."""
    return extract_post_emails(text, allow_free_mail=False)


def extract_post_emails(text: str, *, allow_free_mail: bool = False) -> list[str]:
    """All emails in post text; optional personal domains for LinkedIn content export."""
    text = normalize_obfuscated_email_text(text)
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in WORK_EMAIL.finditer(text):
        email = normalize_email(match.group(1))
        if email in seen:
            continue
        if not allow_free_mail and is_free_mail(email):
            continue
        seen.add(email)
        out.append(email)
    return out


def pick_best_email(text: str) -> tuple[Optional[str], str]:
    """Returns (email, verification_method hint)."""
    careers = extract_from_description(text)
    if careers:
        return careers, "jd_parse"
    for email in extract_work_emails(text):
        local = email.split("@")[0].lower()
        if local in ALLOWED_LOCALS:
            return email, "content_parse"
    return None, "linkedin_export"


def valid_email(email: str) -> bool:
    email = normalize_email(email)
    if not email or "@" not in email:
        return False
    local, domain = email.split("@", 1)
    return bool(local and domain and "." in domain)


def verified_enough(email: str, source: str) -> bool:
    """source: company_csv | jd_parse | content_parse | linkedin_export"""
    email = normalize_email(email)
    if not email or "@" not in email or is_free_mail(email):
        return False
    if source == "company_csv":
        return True
    if source in ("jd_parse", "content_parse"):
        local = email.split("@")[0].lower()
        return local in ALLOWED_LOCALS
    return False
