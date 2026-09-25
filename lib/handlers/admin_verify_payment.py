"""POST /api/admin/verify_payment — mark UPI payment verified and send receipt."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import payment_verify, seekers
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
            utr = (data.get("utr") or "").strip()
            if not seeker_id or not email:
                send_json(self, 400, {"error": "seeker_id and email required"})
                return

            row = seekers.latest_by_id(seeker_id)
            name = (data.get("name") or (row or {}).get("name") or "").strip()
            if not utr and row:
                utr = row.get("utr") or ""

            result = payment_verify.mark_payment_verified(
                seeker_id, email, name=name, utr=utr
            )
            send_json(self, 200, result)
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
