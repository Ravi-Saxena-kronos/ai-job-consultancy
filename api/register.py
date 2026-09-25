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

            seeker_id = (existing or {}).get("seeker_id") or ("APS-" + uuid.uuid4().hex[:6].upper())
            fee = registration_fee_inr()
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
            send_json(self, 500, {"error": str(err)})

    def do_GET(self) -> None:
        send_json(self, 200, {"service": "register", "method": "POST"})
