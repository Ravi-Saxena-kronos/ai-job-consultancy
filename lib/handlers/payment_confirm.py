"""POST /api/payment/confirm — verify Razorpay client signature (instant, no webhook wait)."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import payment_verify, razorpay_client, seekers
from lib.http_util import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if not razorpay_client.enabled():
            send_json(self, 503, {"error": "online payment not configured"})
            return
        try:
            data = read_json(self)
            seeker_id = (data.get("seeker_id") or "").strip()
            order_id = (data.get("razorpay_order_id") or data.get("order_id") or "").strip()
            payment_id = (data.get("razorpay_payment_id") or data.get("payment_id") or "").strip()
            signature = (data.get("razorpay_signature") or data.get("signature") or "").strip()
            if not seeker_id or not order_id or not payment_id or not signature:
                send_json(self, 400, {"error": "missing payment fields"})
                return
            if not razorpay_client.verify_payment_signature(order_id, payment_id, signature):
                send_json(self, 400, {"error": "invalid signature"})
                return

            row = seekers.latest_by_id(seeker_id)
            if not row:
                send_json(self, 404, {"error": "seeker not found"})
                return
            stored_order = (row.get("utr") or "").strip()
            if stored_order and stored_order != order_id:
                send_json(self, 400, {"error": "order mismatch"})
                return

            email = (row.get("email") or "").strip().lower()
            result = payment_verify.mark_payment_verified(
                seeker_id, email, name=(row.get("name") or ""), utr=payment_id
            )
            send_json(self, 200, result)
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
