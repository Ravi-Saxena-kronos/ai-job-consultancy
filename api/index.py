"""Single Vercel Python entry — all /api/* routes (see vercel.json rewrites)."""

from __future__ import annotations

import lib.bootstrap_path  # noqa: F401
from http.server import BaseHTTPRequestHandler

from lib.router import dispatch


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        dispatch(self, "GET")

    def do_POST(self) -> None:
        dispatch(self, "POST")
