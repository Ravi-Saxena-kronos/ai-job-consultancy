"""GET /api/payment/status?seeker_id= — poll after Razorpay checkout."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from lib import seekers
from lib.http_util import send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        seeker_id = (qs.get("seeker_id") or [""])[0].strip()
        if not seeker_id:
            send_json(self, 400, {"error": "seeker_id required"})
            return
        row = seekers.latest_by_id(seeker_id)
        if not row:
            send_json(self, 404, {"error": "not found"})
            return
        send_json(
            self,
            200,
            {
                "seeker_id": seeker_id,
                "payment_status": row.get("payment_status") or "pending",
                "status": row.get("status") or "",
            },
        )
