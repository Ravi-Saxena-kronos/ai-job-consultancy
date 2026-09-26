"""Apply LinkedIn-exported leads from JOB_APPLICATIONS for active seekers."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import email_send, hr_verify, sheets


def _today() -> str:
    return dt.date.today().isoformat()


def iter_linkedin_leads(seeker_id: str) -> list[tuple[int, dict[str, str]]]:
    """1-based sheet row index + row dict."""
    seeker_id = seeker_id.strip()
    out: list[tuple[int, dict[str, str]]] = []
    tab = sheets.applications_tab_name()
    rows = sheets.read_tab(tab)
    if not rows:
        return out
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    for i, row in enumerate(rows[1:], start=2):
        padded = row + [""] * (len(headers) - len(row))
        data = {headers[j]: padded[j] for j in range(len(headers))}
        if (data.get("seeker_id") or "").strip() != seeker_id:
            continue
        if (data.get("status") or "").strip().lower() != "linkedin_lead":
            continue
        out.append((i, data))
    return out


def apply_linkedin_leads_for_seeker(
    seeker: dict[str, str],
    *,
    posts_left: int,
) -> dict[str, int]:
    seeker_id = (seeker.get("seeker_id") or "").strip()
    seeker_email = (seeker.get("email") or "").strip()
    seeker_name = (seeker.get("name") or "").strip()
    resume_url = (seeker.get("resume_url") or "").strip()
    applied = 0
    skipped = 0

    for row_index, row in iter_linkedin_leads(seeker_id):
        if posts_left <= 0:
            break
        hr_email = (row.get("hr_email") or "").strip()
        method = (row.get("verification_method") or "linkedin_export").strip()
        if not hr_email or not hr_verify.verified_enough(hr_email, method):
            skipped += 1
            continue
        title = (row.get("title") or "").strip()
        company = (row.get("company") or "").strip()
        app_id = (row.get("application_id") or "").strip()
        cover = (
            f"Please consider this application for {title}. "
            f"The candidate's experience aligns with the role requirements."
        )
        email_send.hr_application_email(hr_email, title, seeker_name, resume_url, cover)
        email_send.candidate_applied_email(seeker_email, company, title, app_id)
        sheets.update_tab_row(
            sheets.applications_tab_name(),
            row_index,
            [
                app_id,
                seeker_id,
                title,
                company,
                row.get("location") or "",
                row.get("job_url") or "",
                hr_email,
                "Y",
                method,
                "applied",
                _today(),
                "sent",
            ],
        )
        applied += 1
        posts_left -= 1

    return {"linkedin_applied": applied, "linkedin_skipped": skipped, "posts_left": posts_left}
