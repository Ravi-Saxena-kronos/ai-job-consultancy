"""GET /api/cron/process — Vercel cron: Adzuna match, HR verify, apply, notify."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import process as batch
from lib.config import env
from lib.http_util import bearer_secret, send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        secret = bearer_secret(self, "CRON_SECRET") or bearer_secret(self, "ADMIN_SECRET") or ""
        cron = env("CRON_SECRET")
        admin = env("ADMIN_SECRET")
        allowed = {s for s in (cron, admin) if s}
        if allowed and secret not in allowed:
            send_json(self, 401, {"error": "unauthorized"})
            return
        try:
            results = batch.run_batch()
            send_json(self, 200, {"ok": True, "results": results})
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
