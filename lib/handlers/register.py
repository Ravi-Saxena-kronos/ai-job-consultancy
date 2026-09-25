"""POST /api/register — after Amazon Pay UPI, collect email + UTR."""

from __future__ import annotations

import datetime as dt
import uuid

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import email_send, sheets, seekers
from lib.config import registration_fee_inr
from lib.http_util import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            data = read_json(self)
            email = (data.get("email") or "").strip().lower()
            name = (data.get("name") or "").strip()
            utr = (data.get("utr") or data.get("upi_reference") or "").strip()
            if not email or "@" not in email:
                send_json(self, 400, {"error": "valid email required"})
                return
            if not utr:
                send_json(self, 400, {"error": "UPI UTR / reference required"})
                return

            utr = seekers.normalize_utr(utr)
            if len(utr) < 6:
                send_json(self, 400, {"error": "UPI UTR looks too short"})
                return

            by_utr = seekers.latest_by_utr(utr)
            if by_utr:
                owner = (by_utr.get("email") or "").strip().lower()
                if owner != email:
                    send_json(
                        self,
                        409,
                        {
                            "error": "This UTR is already used for another registration.",
                        },
                    )
                    return
                send_json(
                    self,
                    200,
                    {
                        "seeker_id": by_utr.get("seeker_id"),
                        "payment_status": by_utr.get("payment_status") or "pending",
                        "message": "Already submitted with this UTR. No duplicate entry created.",
                        "duplicate": True,
                    },
                )
                return

            existing = seekers.latest_by_email(email)
            if existing and (existing.get("payment_status") or "").lower() == "verified":
                send_json(
                    self,
                    200,
                    {
                        "seeker_id": existing.get("seeker_id"),
                        "payment_status": "verified",
                        "message": "Already registered. Check email for upload steps.",
                    },
                )
                return

            if existing and (existing.get("payment_status") or "").lower() == "pending":
                send_json(
                    self,
                    200,
                    {
                        "seeker_id": existing.get("seeker_id"),
                        "payment_status": "pending",
                        "message": "Registration already pending for this email. Wait for payment verify.",
                        "duplicate": True,
                    },
                )
                return

            seeker_id = (existing or {}).get("seeker_id") or ("APS-" + uuid.uuid4().hex[:6].upper())
            fee = registration_fee_inr()
            sheets.ensure_workbook_tabs()
            sheets.append_row(
                "SEEKERS",
                [
                    seeker_id,
                    email,
                    name,
                    "Y",
                    utr,
                    "pending",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "0",
                    "pending_payment",
                    dt.date.today().isoformat(),
                ],
            )
            try:
                email_send.receipt_email(email, seeker_id, utr)
            except Exception:
                pass
            try:
                email_send.admin_pending_payment_email(seeker_id, name, email, utr)
            except Exception:
                pass
            send_json(
                self,
                200,
                {
                    "seeker_id": seeker_id,
                    "fee_inr": fee,
                    "payment_status": "pending",
                    "message": "Registration recorded. Payment auto-verifies online or via admin for UPI.",
                },
            )
        except Exception as err:
            msg = str(err)
            if "GOOGLE_SERVICE_ACCOUNT_JSON" in msg or "Extra data" in msg:
                msg = (
                    "Server setup error (Google credentials). "
                    "Fix GOOGLE_SERVICE_ACCOUNT_JSON in Vercel: one line only, no text after the closing }."
                )
            elif "does not have permission" in msg or "HttpError 403" in msg:
                msg = (
                    "Google Sheet access denied. Share the spreadsheet with the service account "
                    "client_email as Editor. Remove wrong SHEET_SEEKERS / SHEET_* env vars in Vercel."
                )
            elif "Unable to parse range" in msg or "HttpError 400" in msg:
                msg = (
                    "Google Sheet tab missing. In your spreadsheet add tabs named SEEKERS, "
                    "JOB_APPLICATIONS, COMPANY_VERIFIED (or open /admin.html → Init Google Sheet tabs), then retry."
                )
            send_json(self, 500, {"error": msg})

    def do_GET(self) -> None:
        send_json(self, 200, {"service": "register", "method": "POST"})
