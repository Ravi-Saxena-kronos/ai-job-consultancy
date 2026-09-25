"""Mark seeker payment verified and notify (shared by admin + webhooks)."""

from __future__ import annotations

import datetime as dt

from . import email_send, seekers, sheets


def mark_payment_verified(
    seeker_id: str,
    email: str,
    *,
    name: str = "",
    utr: str = "",
) -> dict:
    row = seekers.latest_by_id(seeker_id)
    if row and (row.get("payment_status") or "").lower() == "verified":
        return {"seeker_id": seeker_id, "payment_status": "verified", "already": True}

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
    email_warning = None
    try:
        email_send.payment_verified_email(email, seeker_id)
    except Exception as err:
        email_warning = str(err)
    out = {"seeker_id": seeker_id, "payment_status": "verified"}
    if email_warning:
        out["email_warning"] = email_warning
    return out
