"""Isolated test applies — TESTING tab + JOB_APPLICATIONS rows with testing=Y."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Optional

from . import adzuna, email_send, hr_verify, sheets
from .config import test_hr_redirect, test_lab_max_applies
from .linkedin_export import application_row_from_sheet
from .tailored_apply import ResumeCache


def _today() -> str:
    return dt.date.today().isoformat()


def _testing_rows() -> list[dict[str, str]]:
    return sheets.rows_as_dicts("TESTING")


def latest_testing_by_id(test_id: str) -> Optional[dict[str, str]]:
    test_id = test_id.strip().upper()
    matches = [r for r in _testing_rows() if (r.get("test_id") or "").strip().upper() == test_id]
    return matches[-1] if matches else None


def testing_row_values(**fields: str) -> list[str]:
    from . import sheet_schema

    headers = sheet_schema.TESTING_HEADERS
    merged = {h: "" for h in headers}
    for key, val in fields.items():
        if key in merged:
            merged[key] = str(val)
    return [merged[h] for h in headers]


def register_test_profile(data: dict[str, str]) -> dict[str, Any]:
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    resume_url = (data.get("resume_url") or "").strip()
    target_role = (data.get("target_role") or "").strip()
    if not name or not email or not resume_url or not target_role:
        return {"ok": False, "error": "name, email, resume_url, and target_role are required"}

    try:
        max_applies = int(data.get("max_applies") or test_lab_max_applies())
    except ValueError:
        max_applies = test_lab_max_applies()
    max_applies = max(1, min(15, max_applies))

    test_id = "TST-" + uuid.uuid4().hex[:8].upper()
    sheets.append_row(
        "TESTING",
        testing_row_values(
            test_id=test_id,
            name=name,
            email=email,
            resume_url=resume_url,
            target_role=target_role,
            domain=(data.get("domain") or "").strip(),
            location=(data.get("location") or "Delhi NCR").strip(),
            experience_years=str(data.get("experience_years") or "").strip(),
            max_applies=str(max_applies),
            status="submitted",
            created_at=_today(),
            last_run_at="",
            notes=(data.get("notes") or "test lab").strip(),
        ),
    )
    return {"ok": True, "test_id": test_id, "max_applies": max_applies}


def _update_testing_row(test_id: str, **kwargs: str) -> None:
    row_index = sheets.find_row_index("TESTING", "test_id", test_id)
    if not row_index:
        return
    row = latest_testing_by_id(test_id) or {}
    sheets.update_row(
        "TESTING",
        row_index,
        testing_row_values(
            test_id=test_id,
            name=row.get("name") or "",
            email=row.get("email") or "",
            resume_url=row.get("resume_url") or "",
            target_role=row.get("target_role") or "",
            domain=row.get("domain") or "",
            location=row.get("location") or "",
            experience_years=row.get("experience_years") or "",
            max_applies=row.get("max_applies") or str(test_lab_max_applies()),
            status=kwargs.get("status", row.get("status") or ""),
            created_at=row.get("created_at") or "",
            last_run_at=kwargs.get("last_run_at", row.get("last_run_at") or ""),
            notes=kwargs.get("notes", row.get("notes") or ""),
        ),
    )


def run_test_applies(test_id: str) -> dict[str, Any]:
    profile = latest_testing_by_id(test_id)
    if not profile:
        return {"ok": False, "error": "test_id not found on TESTING tab"}

    if not email_send.email_configured():
        return {"ok": False, "error": "email not configured"}

    try:
        limit = int(profile.get("max_applies") or test_lab_max_applies())
    except ValueError:
        limit = test_lab_max_applies()
    limit = max(1, min(15, limit))

    _update_testing_row(test_id, status="running", last_run_at=_today(), notes="run started")

    seeker_name = (profile.get("name") or "").strip()
    seeker_email = (profile.get("email") or "").strip()
    resume_url = (profile.get("resume_url") or "").strip()
    seeker_role = (profile.get("target_role") or "").strip()
    location = (profile.get("location") or "Delhi").strip()
    redirect = test_hr_redirect()

    companies = sheets.rows_as_dicts("COMPANIES")
    cache = ResumeCache()
    applied = 0
    skipped = 0
    mail_sent: list[dict[str, str]] = []

    jobs = adzuna.search_jobs(what=seeker_role, where=location, limit=limit + 15)
    for job in jobs:
        if applied >= limit:
            break
        company = job["company"]
        title = job["title"]
        hr_email = sheets.find_verified_company_email(company, companies)
        source = "company_csv"
        if not hr_email:
            hr_email = hr_verify.extract_from_description(job.get("description") or "")
            source = "jd_parse"
        if not hr_email or not hr_verify.verified_enough(hr_email, source):
            skipped += 1
            continue

        send_hr = redirect if redirect and hr_verify.valid_email(redirect) else hr_email
        app_id = "TSTAPP-" + uuid.uuid4().hex[:8].upper()
        job_text = (job.get("description") or "") or f"{title}\n{company}"

        from . import tailored_apply

        result = tailored_apply.send_tailored_application(
            seeker_name=seeker_name,
            seeker_email=seeker_email,
            seeker_role=seeker_role,
            resume_url=resume_url,
            resume_cache=cache,
            hr_email=send_hr,
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
                    "company": company,
                    "status": "failed",
                    "error": str(result.get("error") or "")[:200],
                }
            )
            continue

        method = "test_lab" + ("_redirect" if send_hr != hr_email else "")
        sheets.append_row(
            "APPLICATIONS",
            application_row_from_sheet(
                {},
                application_id=app_id,
                seeker_id=test_id,
                title=title,
                company=company,
                location=job.get("location") or "",
                job_url=job.get("job_url") or "",
                hr_email=send_hr,
                email_verified="Y",
                verification_method=method,
                status="applied",
                applied_at=_today(),
                hr_message_id=result.get("hr_message_id") or "sent",
                tailored_sent=result.get("tailored_sent") or "Y",
                docx_filename=result.get("docx_filename") or "",
                testing="Y",
            ),
        )
        applied += 1
        mail_sent.append(
            {
                "application_id": app_id,
                "company": company,
                "title": title,
                "hr_email": send_hr,
                "status": "mail_sent",
                "docx_filename": result.get("docx_filename") or "",
                "testing": "Y",
            }
        )

    note = f"applied={applied}, skipped={skipped}"
    if redirect:
        note += f"; HR redirect={redirect}"
    _update_testing_row(
        test_id,
        status="completed" if applied else "failed",
        last_run_at=_today(),
        notes=note,
    )
    return {
        "ok": True,
        "test_id": test_id,
        "applied": applied,
        "skipped": skipped,
        "hr_redirect": redirect or None,
        "mail_sent": mail_sent,
    }
