"""POST /api/upload — resume details after payment verified."""

from __future__ import annotations

import datetime as dt

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib import email_send, seekers, sheets
from lib.config import default_posts_remaining
from lib.http_util import read_json, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            data = read_json(self)
            seeker_id = (data.get("seeker_id") or "").strip()
            email = (data.get("email") or "").strip().lower()
            resume_note = (data.get("resume_url") or data.get("resume_note") or "").strip()
            domain = (data.get("domain") or "").strip()
            experience = str(data.get("experience_years") or "").strip()
            target_role = (data.get("target_role") or "").strip()
            location = (data.get("location") or "Delhi NCR").strip()
            name = (data.get("name") or "").strip()

            if not seeker_id or not email:
                send_json(self, 400, {"error": "seeker_id and email required"})
                return

            row = seekers.latest_by_id(seeker_id)
            if not row:
                send_json(self, 404, {"error": "seeker_id not found"})
                return
            if (row.get("email") or "").strip().lower() != email:
                send_json(self, 400, {"error": "email does not match seeker_id"})
                return
            if (row.get("payment_status") or "").lower() != "verified":
                send_json(self, 402, {"error": "payment not verified yet"})
                return

            posts = default_posts_remaining()
            sheets.append_row(
                "SEEKERS",
                [
                    seeker_id,
                    email,
                    name or row.get("name") or "",
                    "Y",
                    row.get("utr") or "",
                    "verified",
                    resume_note,
                    domain,
                    experience,
                    target_role,
                    location,
                    str(posts),
                    "active",
                    dt.date.today().isoformat(),
                ],
            )
            try:
                email_send.resume_received_email(email, seeker_id)
            except Exception:
                pass

            send_json(
                self,
                200,
                {
                    "seeker_id": seeker_id,
                    "status": "active",
                    "posts_remaining": posts,
                },
            )
        except Exception as err:
            send_json(self, 500, {"error": str(err)})
