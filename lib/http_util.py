"""Helpers for Vercel Python HTTP handlers."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any, Optional


def read_json(handler: BaseHTTPRequestHandler, max_bytes: int = 1_000_000) -> dict[str, Any]:
    cl = handler.headers.get("Content-Length")
    if cl is not None:
        length = int(cl)
        if length > max_bytes:
            raise ValueError("body too large")
        raw = handler.rfile.read(length) if length else b"{}"
    else:
        raw = handler.rfile.read(max_bytes)
        if not raw:
            raw = b"{}"
    data = json.loads(raw.decode("utf-8", errors="replace") or "{}")
    return data if isinstance(data, dict) else {}


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def bearer_secret(handler: BaseHTTPRequestHandler, env_name: str) -> Optional[str]:
    auth = handler.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return handler.headers.get(f"X-{env_name.replace('_', '-')}")
