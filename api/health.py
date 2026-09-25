"""GET /api/health — deploy check."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib.http_util import send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        send_json(self, 200, {"ok": True, "service": "ai-job-consultancy"})
