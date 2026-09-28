"""POST /api/test/run — tailor + apply for a TESTING row only."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import test_apply
from lib.config import test_lab_enabled, test_lab_secret
from lib.http_util import bearer_secret, read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if not test_lab_enabled():
            send_json(self, 404, {"error": "test lab disabled"})
            return
        secret = bearer_secret(self, "TEST_LAB_SECRET") or bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != test_lab_secret() or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        try:
            body = read_json(self)
        except ValueError:
            send_json(self, 400, {"error": "invalid json"})
            return
        test_id = (body.get("test_id") or "").strip()
        if not test_id:
            send_json(self, 400, {"error": "test_id required"})
            return
        result = test_apply.run_test_applies(test_id)
        send_json(self, 200 if result.get("ok") else 400, result)
