"""GET /api/admin/pending — list seekers awaiting payment verification."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import seekers
from lib.config import env
from lib.http_util import bearer_secret, send_json


def _latest_by_id() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for row in seekers.all_seeker_rows():
        sid = (row.get("seeker_id") or "").strip()
        if sid:
            by_id[sid] = row
    return by_id


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        secret = bearer_secret(self, "ADMIN_SECRET") or ""
        if secret != env("ADMIN_SECRET") or not secret:
            send_json(self, 401, {"error": "unauthorized"})
            return
        pending = []
        for sid, row in _latest_by_id().items():
            if (row.get("payment_status") or "").lower() != "pending":
                continue
            pending.append(
                {
                    "seeker_id": sid,
                    "email": row.get("email") or "",
                    "name": row.get("name") or "",
                    "utr": row.get("utr") or "",
                    "status": row.get("status") or "",
                    "created_at": row.get("created_at") or "",
                }
            )
        pending.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        send_json(self, 200, {"pending": pending, "count": len(pending)})
