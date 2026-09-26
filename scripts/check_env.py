#!/usr/bin/env python3
"""Validate .env before deploy (no network calls)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.config import env  # noqa: E402
from lib import razorpay_client  # noqa: E402
from lib.email_delivery import email_configured, email_provider  # noqa: E402

REQUIRED = [
    "GOOGLE_SHEET_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "EMAIL_FROM",
    "ADMIN_SECRET",
    "CRON_SECRET",
    "PUBLIC_BASE_URL",
]

RECOMMENDED = [
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "ADMIN_NOTIFY_EMAIL",
]


def main() -> int:
    errors = []
    for key in REQUIRED:
        if not env(key):
            errors.append(f"missing {key}")
    if not email_configured():
        errors.append(
            "missing email delivery: set BREVO_API_KEY, RESEND_API_KEY, or SMTP_HOST+SMTP_PASSWORD"
        )
    raw = env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            json.loads(raw)
        except json.JSONDecodeError:
            errors.append("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")
    if razorpay_client.enabled() and not env("RAZORPAY_WEBHOOK_SECRET"):
        print("warn: RAZORPAY_WEBHOOK_SECRET empty — use confirm API or set webhook secret")
    for key in RECOMMENDED:
        if not env(key):
            print(f"warn: optional {key} not set")
    if errors:
        for e in errors:
            print("error:", e)
        return 1
    print("ok: required env vars present")
    print(f"ok: email provider={email_provider()}")
    if razorpay_client.enabled():
        print("ok: Razorpay online payment enabled")
    else:
        print("info: Amazon Pay UPI mode — use admin.html to verify UTR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
