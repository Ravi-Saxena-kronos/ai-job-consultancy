#!/usr/bin/env python3
"""Email provider selection (no network)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.email_delivery import (  # noqa: E402
    email_configured,
    email_provider,
    resolved_from_email,
    resolved_from_email_source,
)


def _clear_email_env() -> None:
    for key in (
        "EMAIL_PROVIDER",
        "RESEND_API_KEY",
        "BREVO_API_KEY",
        "SMTP_HOST",
        "EMAIL_FROM",
        "ADMIN_NOTIFY_EMAIL",
        "BREVO_SENDER_EMAIL",
    ):
        os.environ.pop(key, None)


def test_auto_brevo_when_no_resend() -> None:
    _clear_email_env()
    os.environ["BREVO_API_KEY"] = "xkeysib-test"
    os.environ["EMAIL_FROM"] = "you@gmail.com"
    assert email_provider() == "brevo"
    assert email_configured()
    _clear_email_env()


def test_auto_resend_first() -> None:
    _clear_email_env()
    os.environ["RESEND_API_KEY"] = "re_test"
    os.environ["BREVO_API_KEY"] = "xkeysib-test"
    os.environ["EMAIL_FROM"] = "noreply@example.com"
    assert email_provider() == "resend"
    _clear_email_env()


def test_display_name_email_from_uses_admin_notify() -> None:
    _clear_email_env()
    os.environ["BREVO_API_KEY"] = "xkeysib-test"
    os.environ["EMAIL_FROM"] = "AI-job-consultancy"
    os.environ["ADMIN_NOTIFY_EMAIL"] = "you@gmail.com"
    assert resolved_from_email() == "you@gmail.com"
    assert resolved_from_email_source() == "ADMIN_NOTIFY_EMAIL"
    assert email_configured()
    _clear_email_env()


def test_explicit_brevo() -> None:
    _clear_email_env()
    os.environ["EMAIL_PROVIDER"] = "brevo"
    os.environ["BREVO_API_KEY"] = "xkeysib-test"
    os.environ["RESEND_API_KEY"] = "re_test"
    os.environ["EMAIL_FROM"] = "you@gmail.com"
    assert email_provider() == "brevo"
    _clear_email_env()


def main() -> int:
    test_display_name_email_from_uses_admin_notify()
    test_auto_brevo_when_no_resend()
    test_auto_resend_first()
    test_explicit_brevo()
    print("ok: test_email_delivery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
