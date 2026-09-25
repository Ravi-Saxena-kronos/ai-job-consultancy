"""WhatsApp / manual notify when email (Resend) is not set up."""

from __future__ import annotations

from .config import env


def upload_url(seeker_id: str) -> str:
    base = (env("PUBLIC_BASE_URL") or "https://ai-job-consultancy.vercel.app").rstrip("/")
    return f"{base}/?seeker_id={seeker_id}#upload"


def whatsapp_payment_verified(name: str, seeker_id: str, email: str, link: str | None = None) -> str:
    link = link or upload_url(seeker_id)
    greeting = f"Hi {name}," if name else "Hi,"
    return (
        f"{greeting}\n\n"
        "Your AI Job Consultancy registration payment is verified.\n\n"
        f"Seeker ID: {seeker_id}\n"
        f"Registered email: {email}\n\n"
        "Upload your resume and job details here:\n"
        f"{link}\n\n"
        "Open the link on your phone, scroll to Step 3, and use the same email you registered with.\n\n"
        "We do not guarantee HR contact or selection."
    )
