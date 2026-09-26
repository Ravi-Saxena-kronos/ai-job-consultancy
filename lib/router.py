"""Route /api/* to handler modules (single Vercel Python function)."""

from __future__ import annotations

import importlib
from http.server import BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import parse_qs, urlparse

from lib.http_util import send_json

# Path (no query) -> module under lib.handlers
ROUTES: dict[str, str] = {
    "/api/health": "lib.handlers.health",
    "/api/public_config": "lib.handlers.public_config",
    "/api/register": "lib.handlers.register",
    "/api/upload": "lib.handlers.upload",
    "/api/admin/pending": "lib.handlers.admin_pending",
    "/api/admin/verify_payment": "lib.handlers.admin_verify_payment",
    "/api/admin/init_sheet": "lib.handlers.admin_init_sheet",
    "/api/admin/resend_email": "lib.handlers.admin_resend_email",
    "/api/admin/test_email": "lib.handlers.admin_test_email",
    "/api/admin/whatsapp": "lib.handlers.admin_whatsapp",
    "/api/cron/process": "lib.handlers.cron_process",
    "/api/payment/checkout": "lib.handlers.payment_checkout",
    "/api/payment/confirm": "lib.handlers.payment_confirm",
    "/api/payment/status": "lib.handlers.payment_status",
    "/api/payment/razorpay_webhook": "lib.handlers.payment_razorpay_webhook",
}


def normalize_path(path: str) -> str:
    p = urlparse(path).path
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p


def request_path(handler: BaseHTTPRequestHandler) -> str:
    """Original URL path (rewrites may set self.path to /api/index)."""
    parsed = urlparse(handler.path)
    qs = parse_qs(parsed.query)
    for key in ("__path", "path"):
        parts = qs.get(key) or []
        if parts and parts[0].strip():
            segment = parts[0].strip().lstrip("/")
            return normalize_path("/api/" + segment)

    for name in (
        "x-vercel-original-path",
        "x-original-path",
        "x-forwarded-uri",
        "x-matched-path",
        "x-invoke-path",
    ):
        val = handler.headers.get(name) or handler.headers.get(name.replace("-", "_").title())
        if val:
            return normalize_path(urlparse(val).path if "://" in val or val.startswith("/") else val)
    return normalize_path(parsed.path)


def handler_module(path: str) -> Optional[str]:
    return ROUTES.get(normalize_path(path))


def dispatch(parent: BaseHTTPRequestHandler, method: str) -> None:
    path = request_path(parent)
    mod_name = handler_module(path)
    if not mod_name:
        send_json(
            parent,
            404,
            {"error": "not found", "path": path},
        )
        return
    try:
        mod = importlib.import_module(mod_name)
        hcls = mod.handler
        fn = getattr(hcls, f"do_{method}", None)
        if not fn:
            send_json(parent, 405, {"error": f"method {method} not allowed"})
            return
        # Call route handler with Vercel's request object (parent), not a nested instance.
        fn(parent)
    except Exception as err:
        send_json(
            parent,
            500,
            {
                "error": str(err),
                "path": path,
                "hint": "Check Vercel logs. For test email set BREVO_API_KEY + EMAIL_FROM + EMAIL_PROVIDER=brevo.",
            },
        )
