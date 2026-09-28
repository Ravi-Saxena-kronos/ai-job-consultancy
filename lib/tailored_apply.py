"""Tailor resume per job and send DOCX to HR + candidate."""

from __future__ import annotations

from typing import Any, Optional

from . import email_send, resume_docx, resume_fetch, resume_tailor


class ResumeCache:
    def __init__(self) -> None:
        self._text: Optional[str] = None
        self._error: Optional[str] = None
        self._url: Optional[str] = None

    def load(self, resume_url: str) -> tuple[str, str]:
        url = (resume_url or "").strip()
        if self._url == url and self._text is not None:
            return self._text, ""
        if self._url == url and self._error:
            return "", self._error
        text, err = resume_fetch.fetch_resume_text(url)
        self._url = url
        self._text = text if text else None
        self._error = err or None
        return text, err


def send_tailored_application(
    *,
    seeker_name: str,
    seeker_email: str,
    seeker_role: str,
    resume_url: str,
    resume_cache: ResumeCache,
    hr_email: str,
    title: str,
    company: str,
    app_id: str,
    job_post_text: str,
) -> dict[str, Any]:
    base, err = resume_cache.load(resume_url)
    if not base:
        return {
            "ok": False,
            "error": err or "could not read resume from link",
            "docx_filename": "",
        }

    try:
        tailored = resume_tailor.tailor_resume(base, title, job_post_text, seeker_role)
        docx_bytes = resume_docx.build_tailored_docx(
            tailored,
            seeker_name=seeker_name,
            job_title=title,
            company=company,
        )
        filename = resume_docx.resume_docx_filename(seeker_name, company, app_id)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "docx_filename": ""}

    cover = (
        f"Please consider this application for {title}. "
        f"The candidate's experience aligns with the role requirements. "
        f"Tailored resume attached (DOCX)."
    )
    try:
        hr_msg_id = email_send.hr_application_email_docx(
            hr_email,
            title,
            seeker_name,
            cover,
            filename,
            docx_bytes,
        )
        cand_msg_id = email_send.candidate_tailored_applied_email(
            seeker_email,
            company=company,
            title=title,
            application_id=app_id,
            target_role=seeker_role,
            filename=filename,
            docx_bytes=docx_bytes,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "docx_filename": filename}

    return {
        "ok": True,
        "hr_message_id": hr_msg_id or "",
        "candidate_message_id": cand_msg_id or "",
        "docx_filename": filename,
        "tailored_sent": "Y",
    }
