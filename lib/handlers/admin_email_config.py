"""GET /api/admin/email_config — debug email env (no secrets)."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib.config import env
from lib.email_delivery import (
    email_configured,
    email_provider,
    resolved_from_email,
    resolved_from_email_source,
)
from lib.http_util import bearer_secret, send_json


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[:2]}…@{domain}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        secret = bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != env("ADMIN_SECRET") or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        raw_from = (env("EMAIL_FROM") or "").strip()
        brevo_sender = (env("BREVO_SENDER_EMAIL") or "").strip()
        resolved = resolved_from_email()
        provider = email_provider() or "none"
        looks_like_name = raw_from.lower() in {
            "ai-job-consultancy",
            "ai job consultancy",
        } or (raw_from and "@" not in raw_from)
        send_json(
            self,
            200,
            {
                "ok": True,
                "provider": provider,
                "email_provider_env": env("EMAIL_PROVIDER") or "auto",
                "email_from_raw_length": len(raw_from),
                "email_from_raw_ends_with": raw_from[-6:] if len(raw_from) >= 6 else raw_from,
                "email_from_has_at_sign": "@" in raw_from,
                "email_from_looks_like_display_name": looks_like_name,
                "brevo_sender_email_set": bool(brevo_sender),
                "email_from_resolved": _mask_email(resolved),
                "email_from_resolved_via": resolved_from_email_source() or "none",
                "email_from_valid": bool(resolved and "@" in resolved),
                "brevo_key_set": bool(env("BREVO_API_KEY").strip()),
                "resend_key_set": bool(env("RESEND_API_KEY").strip()),
                "email_configured": email_configured(),
                "hint": (
                    "Set ADMIN_NOTIFY_EMAIL or BREVO_SENDER_EMAIL to your verified Gmail on Vercel, "
                    "then redeploy. EMAIL_FROM can stay as display name; code uses the Gmail env for sending."
                ),
            },
        )
