"""Send JOB_APPLICATIONS rows (LinkedIn export) — HR email from sheet, then notify candidate."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import email_send, hr_verify, sheets

# Rows ready for batch after LinkedIn export (legacy statuses kept for old sheet rows).
PENDING_SEND_STATUSES = frozenset(
    {
        "pending_send",
        "linkedin_lead",
        "skipped_no_email",
    }
)


def _today() -> str:
    return dt.date.today().isoformat()


def _row_ready_to_send(data: dict[str, str]) -> bool:
    status = (data.get("status") or "").strip().lower()
    if status == "applied":
        return False
    if status not in PENDING_SEND_STATUSES:
        return False
    hr = (data.get("hr_email") or "").strip()
    return hr_verify.valid_email(hr)


def iter_sheet_applications(seeker_id: str) -> list[tuple[int, dict[str, str]]]:
    """1-based sheet row index + row dict for this seeker that still need HR send."""
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
        if not _row_ready_to_send(data):
            continue
        out.append((i, data))
    return out


def apply_linkedin_leads_for_seeker(
    seeker: dict[str, str],
    *,
    posts_left: int,
) -> dict[str, Any]:
    seeker_id = (seeker.get("seeker_id") or "").strip()
    seeker_email = (seeker.get("email") or "").strip()
    seeker_name = (seeker.get("name") or "").strip()
    resume_url = (seeker.get("resume_url") or "").strip()
    applied = 0
    skipped = 0
    mail_sent: list[dict[str, str]] = []

    if not email_send.email_configured():
        return {
            "linkedin_applied": 0,
            "linkedin_skipped": 0,
            "posts_left": posts_left,
            "mail_sent": [],
            "error": "email not configured (Brevo/Resend + sender)",
        }

    for row_index, row in iter_sheet_applications(seeker_id):
        if posts_left <= 0:
            break
        hr_email = hr_verify.normalize_email((row.get("hr_email") or "").strip())
        if not hr_verify.valid_email(hr_email):
            skipped += 1
            continue

        title = (row.get("title") or "").strip()
        company = (row.get("company") or "").strip()
        app_id = (row.get("application_id") or "").strip()
        method = (row.get("verification_method") or "linkedin_export").strip()
        cover = (
            f"Please consider this application for {title}. "
            f"The candidate's experience aligns with the role requirements."
        )

        try:
            hr_msg_id = email_send.hr_application_email(
                hr_email, title, seeker_name, resume_url, cover
            )
            cand_msg_id = email_send.candidate_applied_email(
                seeker_email, company, title, app_id
            )
        except Exception as err:
            skipped += 1
            mail_sent.append(
                {
                    "application_id": app_id,
                    "hr_email": hr_email,
                    "company": company,
                    "status": "failed",
                    "error": str(err)[:200],
                }
            )
            continue

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
                row.get("email_verified") or "Y",
                method,
                "applied",
                _today(),
                hr_msg_id or "sent",
            ],
        )
        applied += 1
        posts_left -= 1
        mail_sent.append(
            {
                "application_id": app_id,
                "hr_email": hr_email,
                "company": company,
                "title": title,
                "status": "mail_sent",
                "hr_message_id": hr_msg_id or "",
                "candidate_message_id": cand_msg_id or "",
                "candidate_email": seeker_email,
            }
        )

    return {
        "linkedin_applied": applied,
        "linkedin_skipped": skipped,
        "posts_left": posts_left,
        "mail_sent": mail_sent,
    }
