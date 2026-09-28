"""Send JOB_APPLICATIONS rows (LinkedIn export) — tailored DOCX to HR + candidate."""

from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from . import hr_verify, sheets
from . import tailored_apply
from .linkedin_export import application_row_from_sheet, job_post_text_for_tailoring
from .tailored_apply import ResumeCache


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
    resume_cache: Optional[ResumeCache] = None,
) -> dict[str, Any]:
    from . import email_send

    seeker_id = (seeker.get("seeker_id") or "").strip()
    seeker_email = (seeker.get("email") or "").strip()
    seeker_name = (seeker.get("name") or "").strip()
    resume_url = (seeker.get("resume_url") or "").strip()
    seeker_role = (seeker.get("target_role") or seeker.get("domain") or "").strip()
    cache = resume_cache or ResumeCache()
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
        job_text = job_post_text_for_tailoring(row)

        result = tailored_apply.send_tailored_application(
            seeker_name=seeker_name,
            seeker_email=seeker_email,
            seeker_role=seeker_role,
            resume_url=resume_url,
            resume_cache=cache,
            hr_email=hr_email,
            title=title,
            company=company,
            app_id=app_id,
            job_post_text=job_text,
        )
        if not result.get("ok"):
            skipped += 1
            mail_sent.append(
                {
                    "application_id": app_id,
                    "hr_email": hr_email,
                    "company": company,
                    "status": "failed",
                    "error": str(result.get("error") or "")[:200],
                }
            )
            continue

        hr_msg_id = result.get("hr_message_id") or ""
        cand_msg_id = result.get("candidate_message_id") or ""
        docx_name = result.get("docx_filename") or ""
        tailored = result.get("tailored_sent") or "Y"

        sheets.update_tab_row(
            sheets.applications_tab_name(),
            row_index,
            application_row_from_sheet(
                row,
                hr_email=hr_email,
                status="applied",
                applied_at=_today(),
                hr_message_id=hr_msg_id or "sent",
                tailored_sent=tailored,
                docx_filename=docx_name,
            ),
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
                "hr_message_id": hr_msg_id,
                "candidate_message_id": cand_msg_id,
                "candidate_email": seeker_email,
                "docx_filename": docx_name,
                "tailored_sent": tailored,
            }
        )

    return {
        "linkedin_applied": applied,
        "linkedin_skipped": skipped,
        "posts_left": posts_left,
        "mail_sent": mail_sent,
    }
