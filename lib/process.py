"""Cron: match jobs, verify HR email, apply + notify (candidate only if HR sent)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from . import adzuna, email_send, hr_verify, seekers, sheets


def _today() -> str:
    return dt.date.today().isoformat()


def _already_applied(seeker_id: str, company: str, title: str) -> bool:
    needle_c = company.strip().lower()
    needle_t = title.strip().lower()
    for row in sheets.rows_as_dicts("APPLICATIONS"):
        if (row.get("seeker_id") or "").strip() != seeker_id:
            continue
        if (row.get("company") or "").strip().lower() != needle_c:
            continue
        if (row.get("title") or "").strip().lower() != needle_t:
            continue
        if (row.get("status") or "") == "applied":
            return True
    return False


def process_one_seeker(seeker: dict[str, str]) -> dict[str, Any]:
    try:
        posts_left = int(seeker.get("posts_remaining") or "0")
    except ValueError:
        posts_left = 0
    if posts_left <= 0:
        return {"seeker_id": seeker.get("seeker_id"), "applied": 0, "skipped": 0}

    role = seeker.get("target_role") or seeker.get("domain") or "developer"
    location = seeker.get("location") or "Delhi"
    seeker_id = seeker.get("seeker_id") or ""
    seeker_email = seeker.get("email") or ""
    seeker_name = seeker.get("name") or ""
    resume_url = seeker.get("resume_url") or ""
    companies = sheets.rows_as_dicts("COMPANIES")

    jobs = adzuna.search_jobs(what=role, where=location, limit=posts_left + 10)
    applied = 0
    skipped = 0

    for job in jobs:
        if applied >= posts_left:
            break
        company = job["company"]
        title = job["title"]
        if _already_applied(seeker_id, company, title):
            skipped += 1
            continue

        hr_email = sheets.find_verified_company_email(company, companies)
        source = "company_csv"
        if not hr_email:
            hr_email = hr_verify.extract_from_description(job.get("description") or "")
            source = "jd_parse"

        app_id = "APP-" + uuid.uuid4().hex[:8].upper()
        if not hr_email or not hr_verify.verified_enough(hr_email, source):
            sheets.append_row(
                "APPLICATIONS",
                [
                    app_id,
                    seeker_id,
                    title,
                    company,
                    job.get("location"),
                    job.get("job_url"),
                    hr_email or "",
                    "N",
                    source,
                    "skipped_no_email",
                    _today(),
                    "",
                ],
            )
            skipped += 1
            continue

        cover = (
            f"Please consider this application for {title}. "
            f"The candidate's experience aligns with the role requirements."
        )
        email_send.hr_application_email(
            hr_email,
            title,
            seeker_name,
            resume_url,
            cover,
        )

        sheets.append_row(
            "APPLICATIONS",
            [
                app_id,
                seeker_id,
                title,
                company,
                job.get("location"),
                job.get("job_url"),
                hr_email,
                "Y",
                source,
                "applied",
                _today(),
                "sent",
            ],
        )
        email_send.candidate_applied_email(seeker_email, company, title, app_id)
        applied += 1
        posts_left -= 1

    # Log updated posts count as new seeker row (append-only audit trail)
    if applied or skipped:
        sheets.append_row(
            "SEEKERS",
            [
                seeker_id,
                seeker_email,
                seeker_name,
                seeker.get("paid_reg") or "Y",
                seeker.get("utr") or "",
                "verified",
                resume_url,
                seeker.get("domain") or "",
                seeker.get("experience_years") or "",
                seeker.get("target_role") or "",
                seeker.get("location") or "",
                str(posts_left),
                "completed" if posts_left <= 0 else "active",
                _today(),
            ],
        )

    return {"seeker_id": seeker_id, "applied": applied, "skipped": skipped, "posts_remaining": posts_left}


def run_batch() -> list[dict[str, Any]]:
    results = []
    for row in seekers.active_seekers():
        results.append(process_one_seeker(row))
    return results
