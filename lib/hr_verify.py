"""HR / careers email verification before sending."""

from __future__ import annotations

import re
from typing import Optional

ALLOWED_LOCALS = frozenset({"careers", "jobs", "recruitment", "hr", "talent", "hiring"})

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


def verified_enough(email: str, source: str) -> bool:
    """source: company_csv | jd_parse"""
    email = normalize_email(email)
    if not email or "@" not in email or is_free_mail(email):
        return False
    if source == "company_csv":
        return True
    if source == "jd_parse":
        local = email.split("@")[0].lower()
        return local in ALLOWED_LOCALS
    return False
