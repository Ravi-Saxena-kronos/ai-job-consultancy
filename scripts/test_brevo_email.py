#!/usr/bin/env python3
"""Send one test email using .env (local — no Vercel)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import email_send  # noqa: E402
from lib.config import env  # noqa: E402


def main() -> int:
    to = (sys.argv[1] if len(sys.argv) > 1 else env("ADMIN_NOTIFY_EMAIL") or "").strip()
    if not to or "@" not in to:
        print("Usage: python scripts/test_brevo_email.py you@gmail.com")
        return 2
    if not email_send.email_configured():
        env_path = ROOT / ".env"
        print("error: email not configured.")
        print(f"  Create {env_path} (copy from .env.example) with at least:")
        print("    EMAIL_PROVIDER=brevo")
        print("    BREVO_API_KEY=xkeysib-...")
        print("    EMAIL_FROM=your-verified-gmail@gmail.com")
        print("  Same values as Vercel → Settings → Environment Variables.")
        return 1
    print("provider:", email_send.email_provider())
    print("from:", env("EMAIL_FROM"))
    msg_id = email_send.send_email(to, "AI Job Consultancy — local test", "Local test OK.\n")
    print("ok: message_id=", msg_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
