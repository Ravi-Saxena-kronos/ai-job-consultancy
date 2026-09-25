"""POST /api/admin/test_email — send test via Resend and return full API response."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import email_send
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
            to = (data.get("email") or env("ADMIN_NOTIFY_EMAIL") or "").strip().lower()
            if not to or "@" not in to:
                send_json(
                    self,
                    400,
                    {"error": "Provide email in JSON or set ADMIN_NOTIFY_EMAIL on Vercel"},
                )
                return
            from_addr = env("EMAIL_FROM")
            msg_id = email_send.send_email(
                to,
                "AI Job Consultancy — test email",
                "If you received this, Resend is working for this recipient address.\n",
            )
            send_json(
                self,
                200,
                {
                    "ok": True,
                    "to": to,
                    "from": from_addr,
                    "resend_id": msg_id,
                    "hint": (
                        "Check Resend dashboard → Emails. If id exists but inbox empty, "
                        "check spam. Gmail needs a verified domain on EMAIL_FROM."
                    ),
                },
            )
        except Exception as err:
            send_json(
                self,
                500,
                {
                    "error": str(err),
                    "hint": (
                        "Common fix: verify your domain in Resend; set EMAIL_FROM to "
                        "noreply@yourdomain.com. onboarding@resend.dev only delivers to "
                        "your Resend account email."
                    ),
                },
            )
