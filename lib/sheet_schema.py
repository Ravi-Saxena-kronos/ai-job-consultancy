"""Canonical tab names and header rows for Google Sheets bootstrap."""

from __future__ import annotations

SEEKERS_HEADERS = [
    "seeker_id",
    "email",
    "name",
    "paid_reg",
    "utr",
    "payment_status",
    "resume_url",
    "domain",
    "experience_years",
    "target_role",
    "location",
    "posts_remaining",
    "status",
    "created_at",
]

APPLICATIONS_HEADERS = [
    "application_id",
    "seeker_id",
    "title",
    "company",
    "location",
    "job_url",
    "hr_email",
    "email_verified",
    "verification_method",
    "status",
    "applied_at",
    "hr_message_id",
]

COMPANIES_HEADERS = [
    "company_name",
    "hr_email",
    "verified_on",
    "source",
]

TAB_SPECS: dict[str, list[str]] = {
    "SEEKERS": SEEKERS_HEADERS,
    "APPLICATIONS": APPLICATIONS_HEADERS,
    "COMPANIES": COMPANIES_HEADERS,
}
