"""POST /api/admin/init_sheet — create tabs + header rows (one-time after deploy)."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import sheets
from lib.config import env
from lib.http_util import bearer_secret, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        secret = bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != env("ADMIN_SECRET") or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        try:
            tabs = sheets.ensure_workbook_tabs()
            send_json(self, 200, {"ok": True, "tabs": tabs})
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
