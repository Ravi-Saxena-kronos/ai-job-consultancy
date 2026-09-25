"""POST /api/payment/checkout — Razorpay order for auto-verified registration."""

from __future__ import annotations

import datetime as dt
import uuid

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import razorpay_client, sheets
from lib import seekers
from lib.config import registration_fee_inr
from lib.http_util import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if not razorpay_client.enabled():
            send_json(self, 503, {"error": "online payment not configured"})
            return
        try:
            data = read_json(self)
            email = (data.get("email") or "").strip().lower()
            name = (data.get("name") or "").strip()
            if not email or "@" not in email:
                send_json(self, 400, {"error": "valid email required"})
                return

            existing = seekers.latest_by_email(email)
            if existing and (existing.get("payment_status") or "").lower() == "verified":
                send_json(
                    self,
                    200,
                    {
                        "seeker_id": existing.get("seeker_id"),
                        "payment_status": "verified",
                        "already_paid": True,
                    },
                )
                return

            seeker_id = (existing or {}).get("seeker_id") or ("APS-" + uuid.uuid4().hex[:6].upper())
            order = razorpay_client.create_order(seeker_id, receipt=seeker_id)
            order_id = order.get("id") or ""
            sheets.append_row(
                "SEEKERS",
                [
                    seeker_id,
                    email,
                    name,
                    "Y",
                    order_id,
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
            fee = registration_fee_inr()
            send_json(
                self,
                200,
                {
                    "seeker_id": seeker_id,
                    "order_id": order_id,
                    "amount_inr": fee,
                    "amount_paise": fee * 100,
                    "currency": "INR",
                    "razorpay_key_id": razorpay_client.key_id(),
                },
            )
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
