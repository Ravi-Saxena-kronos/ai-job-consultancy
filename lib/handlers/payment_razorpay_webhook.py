"""POST /api/payment/razorpay_webhook — auto-verify on payment.captured."""

from __future__ import annotations

import json

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import payment_verify, seekers
from lib import razorpay_client
from lib.http_util import send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        sig = self.headers.get("X-Razorpay-Signature") or ""
        if not razorpay_client.verify_webhook_signature(raw, sig):
            send_json(self, 401, {"error": "invalid signature"})
            return
        try:
            payload = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            send_json(self, 400, {"error": "invalid json"})
            return

        event = payload.get("event") or ""
        if event != "payment.captured":
            send_json(self, 200, {"ok": True, "ignored": event or "unknown"})
            return

        entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
        order_id = entity.get("order_id") or ""
        payment_id = entity.get("id") or ""
        notes = entity.get("notes") or {}
        seeker_id = (notes.get("seeker_id") or "").strip()

        if not seeker_id and order_id:
            for row in seekers.all_seeker_rows():
                if (row.get("utr") or "").strip() == order_id:
                    seeker_id = (row.get("seeker_id") or "").strip()
                    break

        if not seeker_id:
            send_json(self, 200, {"ok": True, "warning": "seeker_id not found"})
            return

        row = seekers.latest_by_id(seeker_id)
        email = (row.get("email") or "").strip().lower() if row else ""
        if not email:
            send_json(self, 200, {"ok": True, "warning": "email missing"})
            return

        utr = payment_id or order_id
        result = payment_verify.mark_payment_verified(
            seeker_id, email, name=(row.get("name") or ""), utr=utr
        )
        send_json(self, 200, {"ok": True, **result})
