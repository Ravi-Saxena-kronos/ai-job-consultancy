"""GET /api/public_config — registration fee and UPI wallet (no secrets)."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler
from urllib.parse import quote

from lib import razorpay_client
from lib.config import registration_fee_inr, upi_payee_name, upi_vpa
from lib.http_util import send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        fee = registration_fee_inr()
        vpa = upi_vpa()
        name = upi_payee_name()
        online = razorpay_client.enabled()
        send_json(
            self,
            200,
            {
                "registration_fee_inr": fee,
                "upi_vpa": vpa,
                "upi_provider": "Amazon Pay",
                "payee_name": name,
                "upi_intent_url": (
                    f"upi://pay?pa={quote(vpa)}&pn={quote(name)}&am={fee}&cu=INR"
                ),
                "payment_online": online,
                "razorpay_key_id": razorpay_client.key_id() if online else "",
            },
        )
