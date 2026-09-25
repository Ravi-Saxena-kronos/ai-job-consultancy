"""Route /api/* to handler modules (single Vercel Python function)."""

from __future__ import annotations

import importlib
from http.server import BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlparse

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
    for name in (
        "x-vercel-original-path",
        "x-original-path",
        "x-forwarded-uri",
        "x-matched-path",
    ):
        val = handler.headers.get(name) or handler.headers.get(name.replace("-", "_").title())
        if val:
            return normalize_path(val)
    return normalize_path(handler.path)


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
    mod = importlib.import_module(mod_name)
    hcls = mod.handler
    sub = hcls(parent.request, parent.client_address, parent.server)
    sub.path = parent.path
    sub.headers = parent.headers
    sub.rfile = parent.rfile
    sub.wfile = parent.wfile
    sub.command = parent.command
    sub.request_version = parent.request_version
    fn = getattr(sub, f"do_{method}", None)
    if not fn:
        send_json(parent, 405, {"error": f"method {method} not allowed"})
        return
    fn()
