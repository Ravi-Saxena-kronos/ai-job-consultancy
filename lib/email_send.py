"""Transactional email via Resend HTTP API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import env


def send_email(to: str, subject: str, text: str) -> str:
    """Send via Resend. Returns Resend message id on success."""
    key = env("RESEND_API_KEY")
    from_addr = env("EMAIL_FROM")
    if not key or not from_addr:
        raise RuntimeError("RESEND_API_KEY and EMAIL_FROM must be set on Vercel")

    body = json.dumps(
        {
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "text": text,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as err:
        detail = err.read().decode()
        raise RuntimeError(f"Resend HTTP {err.code}: {detail}") from err
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw or "ok"
    return str(data.get("id") or data.get("message_id") or "ok")


def _upload_url(seeker_id: str) -> str:
    base = (env("PUBLIC_BASE_URL") or "").rstrip("/")
    if not base:
        return f"(open the site and use Step 3 with ID {seeker_id})"
    return f"{base}/?seeker_id={seeker_id}#upload"


def receipt_email(seeker_email: str, seeker_id: str, utr: str) -> str:
    fee = env("REGISTRATION_FEE_INR", "99")
    return send_email(
        seeker_email,
        f"Registration received — Rs {fee}",
        f"Hi,\n\nWe received your registration (ID {seeker_id}). "
        f"Payment reference: {utr or 'pending verification'}.\n\n"
        "We will email you again when payment is verified with your upload link.\n\n"
        "We do not guarantee HR contact or selection.\n",
    )


def payment_verified_email(seeker_email: str, seeker_id: str) -> str:
    link = _upload_url(seeker_id)
    return send_email(
        seeker_email,
        "Payment verified — upload resume",
        f"Hi,\n\nYour registration payment is verified. Your seeker ID is {seeker_id}.\n\n"
        f"Upload resume and job preferences here:\n{link}\n\n"
        "We do not guarantee HR contact or selection.\n",
    )


def admin_pending_payment_email(seeker_id: str, name: str, email: str, utr: str) -> None:
    admin = env("ADMIN_NOTIFY_EMAIL")
    if not admin:
        return
    base = (env("PUBLIC_BASE_URL") or "").rstrip("/")
    admin_link = f"{base}/admin.html" if base else "/admin.html"
    send_email(
        admin,
        f"Pending UPI — {seeker_id}",
        f"New registration needs payment check.\n\n"
        f"ID: {seeker_id}\nName: {name}\nEmail: {email}\nUTR: {utr}\n\n"
        f"One-click verify: {admin_link}\n",
    )


def resume_received_email(seeker_email: str, seeker_id: str) -> None:
    send_email(
        seeker_email,
        "Resume received",
        f"Hi,\n\nYour resume for ID {seeker_id} is on file. "
        "We will email you only when a verified careers address receives your application.\n\n"
        "We do not guarantee HR contact or selection.\n",
    )


def hr_application_email(
    hr_email: str,
    title: str,
    seeker_name: str,
    resume_url: str,
    cover_note: str,
) -> None:
    body = (
        f"Dear Hiring Team,\n\n"
        f"A candidate has applied for: {title}\n"
        f"Candidate: {seeker_name or 'Applicant'}\n\n"
        f"{cover_note}\n\n"
    )
    if resume_url:
        body += f"Resume: {resume_url}\n\n"
    body += "Sent via AI Job Consultancy with the candidate's consent.\n"
    send_email(hr_email, f"Application: {title}", body)


def candidate_applied_email(seeker_email: str, company: str, title: str, application_id: str) -> None:
    send_email(
        seeker_email,
        f"Resume sent — {company}",
        f"Hi,\n\nYour resume was emailed to {company} for the role: {title}.\n"
        f"Reference: {application_id}\n\n"
        "We do not guarantee HR contact or selection.\n",
    )
