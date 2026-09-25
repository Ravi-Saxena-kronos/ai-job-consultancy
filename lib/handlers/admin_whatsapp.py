"""GET /api/admin/whatsapp?seeker_id= — WhatsApp text for verified seeker."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from lib import seeker_notify, seekers
from lib.config import env
from lib.http_util import bearer_secret, send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        secret = bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != env("ADMIN_SECRET") or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        qs = parse_qs(urlparse(self.path).query)
        seeker_id = (qs.get("seeker_id") or [""])[0].strip()
        if not seeker_id:
            send_json(self, 400, {"error": "seeker_id required"})
            return
        row = seekers.latest_by_id(seeker_id)
        if not row:
            send_json(self, 404, {"error": "not found"})
            return
        if (row.get("payment_status") or "").lower() != "verified":
            send_json(self, 400, {"error": "payment not verified yet — click Verify first"})
            return
        email = (row.get("email") or "").strip().lower()
        name = (row.get("name") or "").strip()
        link = seeker_notify.upload_url(seeker_id)
        send_json(
            self,
            200,
            {
                "seeker_id": seeker_id,
                "upload_url": link,
                "whatsapp_message": seeker_notify.whatsapp_payment_verified(
                    name, seeker_id, email, link
                ),
            },
        )
