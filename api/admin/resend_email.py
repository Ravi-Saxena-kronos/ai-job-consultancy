"""POST /api/admin/resend_email — resend payment or upload email to seeker."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import email_send, seekers
from lib.config import env
from lib.http_util import bearer_secret, read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        secret = bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != env("ADMIN_SECRET") or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        try:
            data = read_json(self)
            seeker_id = (data.get("seeker_id") or "").strip()
            email = (data.get("email") or "").strip().lower()
            kind = (data.get("kind") or "auto").strip().lower()

            row = None
            if seeker_id:
                row = seekers.latest_by_id(seeker_id)
            elif email:
                row = seekers.latest_by_email(email)
            if not row:
                send_json(self, 404, {"error": "seeker not found"})
                return

            seeker_id = (row.get("seeker_id") or "").strip()
            email = (row.get("email") or "").strip().lower()
            if not email:
                send_json(self, 400, {"error": "seeker has no email"})
                return

            payment = (row.get("payment_status") or "").lower()
            if kind == "receipt" or (kind == "auto" and payment != "verified"):
                email_send.receipt_email(email, seeker_id, row.get("utr") or "")
                send_json(self, 200, {"ok": True, "sent": "receipt", "seeker_id": seeker_id, "email": email})
                return

            email_send.payment_verified_email(email, seeker_id)
            send_json(
                self,
                200,
                {"ok": True, "sent": "payment_verified", "seeker_id": seeker_id, "email": email},
            )
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
