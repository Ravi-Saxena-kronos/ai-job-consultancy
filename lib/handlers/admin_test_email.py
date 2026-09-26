"""POST /api/admin/test_email — send test email and return API response."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import email_send
from lib.config import env
from lib.email_delivery import resolved_from_email
from lib.http_util import bearer_secret, read_json, send_json


def _provider_hint(provider: str) -> str:
    if provider == "brevo":
        return (
            "Check Brevo → Transactional → Logs. EMAIL_FROM must be a verified sender "
            "(your Gmail works without owning a domain)."
        )
    if provider == "smtp":
        return "Check SMTP provider logs. For Brevo SMTP use smtp-relay.brevo.com and SMTP key."
    return (
        "Check Resend dashboard → Emails. Gmail needs a verified domain on EMAIL_FROM. "
        "onboarding@resend.dev only delivers to your Resend account email."
    )


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
            from_addr = resolved_from_email()
            provider = email_send.email_provider() or "none"
            if not from_addr or "@" not in from_addr:
                send_json(
                    self,
                    400,
                    {
                        "error": "EMAIL_FROM is missing or invalid on Vercel",
                        "hint": "Set EMAIL_FROM to the exact Gmail you verified in Brevo → Senders.",
                    },
                )
                return
            msg_id = email_send.send_email(
                to,
                "AI Job Consultancy — test email",
                f"If you received this, {provider} email is working for this recipient.\n",
            )
            send_json(
                self,
                200,
                {
                    "ok": True,
                    "to": to,
                    "from": from_addr,
                    "provider": provider,
                    "message_id": msg_id,
                    "resend_id": msg_id,
                    "hint": _provider_hint(provider),
                },
            )
        except Exception as err:
            provider = email_send.email_provider() or "none"
            send_json(
                self,
                500,
                {
                    "error": str(err),
                    "provider": provider,
                    "from_resolved": resolved_from_email(),
                    "hint": _provider_hint(provider),
                },
            )
