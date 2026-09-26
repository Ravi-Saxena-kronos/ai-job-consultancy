"""Mark seeker payment verified and notify (shared by admin + webhooks)."""

from __future__ import annotations

import datetime as dt

from . import email_send, seeker_notify, seekers, sheets
from .config import env


def mark_payment_verified(
    seeker_id: str,
    email: str,
    *,
    name: str = "",
    utr: str = "",
) -> dict:
    row = seekers.latest_by_id(seeker_id)
    if row and (row.get("payment_status") or "").lower() == "verified":
        link = seeker_notify.upload_url(seeker_id)
        nm = name or (row.get("name") or "").strip()
        em = email.strip().lower() or (row.get("email") or "").strip().lower()
        return {
            "seeker_id": seeker_id,
            "payment_status": "verified",
            "already": True,
            "upload_url": link,
            "whatsapp_message": seeker_notify.whatsapp_payment_verified(nm, seeker_id, em, link),
            "notify_via": "email",
        }

    email = email.strip().lower()
    if not name and row:
        name = (row.get("name") or "").strip()
    if not utr and row:
        utr = (row.get("utr") or "").strip()

    sheets.append_row(
        "SEEKERS",
        [
            seeker_id,
            email,
            name,
            "Y",
            utr,
            "verified",
            "",
            "",
            "",
            "",
            "",
            "0",
            "pending_resume",
            dt.date.today().isoformat(),
        ],
    )
    link = seeker_notify.upload_url(seeker_id)
    email_warning = None
    if email_send.email_configured():
        try:
            email_send.payment_verified_email(email, seeker_id)
        except Exception as err:
            email_warning = str(err)
    else:
        email_warning = (
            "Email not configured — set EMAIL_FROM plus BREVO_API_KEY (no domain), "
            "RESEND_API_KEY, or SMTP_* on Vercel"
        )

    out = {
        "seeker_id": seeker_id,
        "payment_status": "verified",
        "upload_url": link,
        "whatsapp_message": seeker_notify.whatsapp_payment_verified(name, seeker_id, email, link),
        "notify_via": "email",
        "email_sent": email_warning is None,
    }
    if email_warning:
        out["email_warning"] = email_warning
    return out
