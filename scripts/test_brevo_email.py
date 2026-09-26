#!/usr/bin/env python3
"""Send one test email using .env (local — no Vercel, no Google Sheets)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.config import env  # noqa: E402
from lib.email_delivery import email_configured, email_provider, send_email  # noqa: E402


def _mask(name: str) -> str:
    v = env(name).strip()
    if not v:
        return "(not set)"
    if len(v) <= 8:
        return "(set)"
    return v[:4] + "…" + v[-4:]


def main() -> int:
    env_file = ROOT / ".env"
    print(f".env file: {env_file} {'exists' if env_file.is_file() else 'MISSING'}")
    print(f"  EMAIL_FROM: {_mask('EMAIL_FROM')}")
    print(f"  BREVO_API_KEY: {_mask('BREVO_API_KEY')}")
    print(f"  EMAIL_PROVIDER: {env('EMAIL_PROVIDER') or '(auto)'}")
    print(f"  RESEND_API_KEY: {_mask('RESEND_API_KEY')}")

    to = (sys.argv[1] if len(sys.argv) > 1 else env("ADMIN_NOTIFY_EMAIL") or "").strip()
    if not to or "@" not in to:
        print("\nUsage: python scripts/test_brevo_email.py you@gmail.com")
        return 2
    if not env("BREVO_API_KEY").strip():
        print("\nerror: BREVO_API_KEY is empty in .env")
        print("  Use ONE line only: BREVO_API_KEY=xkeysib-...")
        print("  Remove duplicate BREVO_API_KEY= lines (empty line loads first in old config).")
        return 1
    if not email_configured():
        print("\nerror: email not configured (check EMAIL_FROM).")
        return 1
    print("\nprovider:", email_provider())
    msg_id = send_email(to, "AI Job Consultancy — local test", "Local test OK.\n")
    print("ok: message_id=", msg_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
