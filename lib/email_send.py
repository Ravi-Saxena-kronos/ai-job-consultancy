"""Transactional email templates (delivery via Resend, Brevo, or SMTP)."""

from __future__ import annotations

from .config import env
from .email_delivery import email_configured, email_provider, send_email as deliver

__all__ = [
    "send_email",
    "email_configured",
    "email_provider",
    "receipt_email",
    "payment_verified_email",
    "admin_pending_payment_email",
    "resume_received_email",
    "hr_application_email",
    "candidate_applied_email",
]


def send_email(to: str, subject: str, text: str) -> str:
    return deliver(to, subject, text)


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


def resume_received_email(seeker_email: str, seeker_id: str) -> str:
    return send_email(
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
) -> str:
    body = (
        f"Dear Hiring Team,\n\n"
        f"A candidate has applied for: {title}\n"
        f"Candidate: {seeker_name or 'Applicant'}\n\n"
        f"{cover_note}\n\n"
    )
    if resume_url:
        body += f"Resume: {resume_url}\n\n"
    body += "Sent via AI Job Consultancy with the candidate's consent.\n"
    return send_email(hr_email, f"Application: {title}", body)


def candidate_applied_email(seeker_email: str, company: str, title: str, application_id: str) -> str:
    return send_email(
        seeker_email,
        f"Resume sent — {company}",
        f"Hi,\n\nYour resume was emailed to {company} for the role: {title}.\n"
        f"Reference: {application_id}\n\n"
        "We do not guarantee HR contact or selection.\n",
    )
